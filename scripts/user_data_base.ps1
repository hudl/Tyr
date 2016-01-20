<powershell>
#User Data script
$ErrorActionPreference = "Stop";

Import-Module "C:\Program Files (x86)\AWS Tools\PowerShell\AWSPowerShell\AWSPowerShell.psd1"
Add-Type -Path "C:\Program Files (x86)\AWS Tools\PowerShell\AWSPowerShell\AWSSDK.EC2.dll"
Add-Type -Path "C:\Program Files (x86)\AWS Tools\PowerShell\AWSPowerShell\AWSSDK.S3.dll"

$AwsTools = Get-Module "AWSPowerShell"

$BASE_DIR="C:\hudl"
$CONFIG="$BASE_DIR\config"
$LOG_DIR="$BASE_DIR\script-logs"
$USERDATA_LOG = "$LOG_DIR\user_data.log"
$METADATA_BASEURL = "http://169.254.169.254/latest/meta-data"
$userDataBaseUrl = "http://169.254.169.254/latest/user-data"
$DYNAMICDATA_BASEURL = "http://169.254.169.254/latest/dynamic"
$region = ((Invoke-WebRequest -UseBasicParsing  -Uri $DYNAMICDATA_BASEURL/instance-identity/document ).Content | ConvertFrom-Json).region
$serverNameFilePath = "C:\hudl\config\servername.txt";
$instanceId = (Invoke-WebRequest -Uri $METADATA_BASEURL/instance-id/ -UseBasicParsing ).Content
$REGIONS = @{'ap-northeast-1' = 'apne1'; 
             'ap-southeast-1'= 'apse1';
             'ap-southeast-2'= 'apse2';
             'eu-central-1'= 'euc1';
             'eu-west-1'= 'euw1';
             'sa-east-1'= 'sae1';
             'us-east-1'= 'use1';
             'us-west-1'= 'usw1';
             'us-west-2'= 'usw2'}


Set-DefaultAWSRegion -Region $region
try {
  New-Item $BASE_DIR -type directory
  New-Item $CONFIG -type directory
  New-Item $LOG_DIR -type directory
} catch {}


function New-ServerName {
    $serverId=GetNewId
    $zone = Get-MyAvailabilityZone
    $region = Get-MyRegion
    $zoneLetter = $zone -replace $region, ""
    $role = Get-MyRole
    $regionName = $REGIONS[$region]
    $myName="$role-$($regionName)$zoneLetter-$serverId"
    return $myName
}

function GetNewId
{
    $ticks = [System.DateTime]::Now.Ticks;
    $ticks = $ticks -shr 16;
    $ticks = $ticks -band 0x3fffffff;
    return ZBase32Encode($ticks);
}

try{
    Set-Variable ZBase32Alphabet -Option ReadOnly -Scope script -Value "ybndrfg8ejkmcpqxot1uwisza345h769"
    Set-Variable ZBase32Base -Option ReadOnly -Scope script -Value 32
}catch {}
function ZBase32Encode([long] $number)
{
    if ($number -eq 0)
    {
        return $ZBase32Alphabet[0].ToString();
    }
    $encoded = New-Object System.Text.StringBuilder(64);
    while ($number -gt 0)
    {
        $character = $ZBase32Alphabet[[int]($number % $ZBase32Base)];
        $ignore = $encoded.Insert(0, $character);
        $number = [int][System.Math]::Floor($number / $ZBase32Base);
    }
    
    return $encoded.ToString();
}

function Get-MyAvailabilityZone {
   
    return (Invoke-WebRequest -UseBasicParsing -Uri $METADATA_BASEURL/placement/availability-zone).Content
    
}

function Get-MyRegion {
    return ((Invoke-WebRequest -UseBasicParsing  -Uri $DYNAMICDATA_BASEURL/instance-identity/document ).Content | ConvertFrom-Json).region
}

function Get-MyRole {
    try{
    $result = Invoke-WebRequest -UseBasicParsing -Uri $METADATA_BASEURL/iam/security-credentials/
    $role = $result.Content
    return $role
    } catch {
        return ""
    }
}


### Determine server name and set it
### Generate client.rb
### Install chef
$servername = New-ServerName

# Store and Set servername in config dir
Write-Output $servername | Out-File -FilePath ($CONFIG + "\servername.txt") -ErrorAction Stop
$File = Get-Content "c:\hudl\config\servername.txt"
[System.IO.File]::WriteAllLines("c:\hudl\config\servername_chef", $File)
New-EC2Tag -Region $region -ResourceId $instanceId -Tag @{key="Name"; value="$servername"}

# Install Chef
$chef_tag_role = Get-EC2Tag -Filters @( @{Name="key"; values="Role"}, @{Name="resource-id"; Values=$instanceId})
$chef_environment = Get-EC2Tag -Filters @( @{Name="key"; values="Environment"}, @{Name="resource-id"; Values=$instanceId})
$windows_version = "2012r2"
$chef_version = "chef-client-12.6.0-1-x86.msi"
$server_name = $servername.Trim()
$chef_env = $chef_environment.Value.ToLower().Trim()
$client_rb = @"
base_dir = "C:/Chef"
log_level        :info
log_location     STDOUT
chef_server_url  'https://ec2-54-86-160-148.compute-1.amazonaws.com/organizations/hudl'
node_name  "$server_name"
environment    "$chef_env"
validation_client_name 'hudl-validator'
validation_key "#{base_dir}/validation.pem"
client_key "#{base_dir}/client.pem"
ssl_verify_mode   :verify_none
checksum_path "#{base_dir}/checksum"
file_cache_path "#{base_dir}/cache"
file_backup_path "#{base_dir}/backup"
cache_options({:path => "#{base_dir}/cache/checksums", :skip_expires => true})
"@

try { New-Item c:\temp -type directory } catch {}

# It doesn't appear the windows version matters as there is only one
# msi installer and it is listed for all types of Windows Server
try {
    Invoke-WebRequest "https://opscode-omnibus-packages.s3.amazonaws.com/windows/$windows_version/i386/$chef_version" -OutFile "c:\temp\chef-client.msi"
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/qn /i c:\temp\chef-client.msi ADDLOCAL=`"ChefClientFeature,ChefServiceFeature,ChefPSModuleFeature`"" -Wait -NoNewWindow
    Read-S3Object -BucketName "hudl-chef-artifacts" -KeyPrefix "chef-client" -Folder "c:\chef"
    $format_client_rb = $client_rb -replace '[\u200B]+',''
    $format_client_rb.Trim() | Out-File "c:\chef\client.rb" -Encoding utf8
}
catch [Exception]{
    Write-Output "Failed to install Chef!" | Out-File -FilePath $USERDATA_LOG 
    Write-Output $_.Exception.Message | Out-File -FilePath $USERDATA_LOG -ErrorAction Stop
}

# Run Chef with the Role from the AWS Tag
try {
    $chef_role = "$($chef_tag_role.Value.ToLower())"
    $env:Path += ";C:\opscode\chef\bin"
    Start-Process -FilePath "chef-client" -ArgumentList "-c `"c:\chef\client.rb`" -r `"role[$chef_role]`" -L `"c:\chef\chef-client-initial-run.log`"" -Wait -NoNewWindow
}
catch [Exception]{
    Write-Output "Failed to run Chef!" | Out-File -FilePath $USERDATA_LOG 
    Write-Output $_.Exception.Message | Out-File -FilePath $USERDATA_LOG -ErrorAction Stop
}
</powershell>
<persist>true</persist>
