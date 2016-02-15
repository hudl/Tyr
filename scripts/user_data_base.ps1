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

# ----------------------------------------------------------------------------------------------
# download a file
# ----------------------------------------------------------------------------------------------
Function Download-File {
Param (
    [Parameter(Mandatory=$True)] [System.Uri]$uri,
    [Parameter(Mandatory=$True )] [string]$FilePath
)

#Make sure the destination directory exists
#System.IO.FileInfo works even if the file/dir doesn't exist, which is better then get-item which requires the file to exist
If (! ( Test-Path ([System.IO.FileInfo]$FilePath).DirectoryName ) ) { [void](New-Item ([System.IO.FileInfo]$FilePath).DirectoryName -force -type directory)}

#see if this file exists
if ( -not (Test-Path $FilePath) ) {
    #use simple download
    [void] (New-Object System.Net.WebClient).DownloadFile($uri.ToString(), $FilePath)
} else {
    try {
        #use HttpWebRequest to download file
        $webRequest = [System.Net.HttpWebRequest]::Create($uri);
        $webRequest.IfModifiedSince = ([System.IO.FileInfo]$FilePath).LastWriteTime
        $webRequest.Method = "GET";
        [System.Net.HttpWebResponse]$webResponse = $webRequest.GetResponse()

        #Read HTTP result
        $stream = New-Object System.IO.StreamReader($response.GetResponseStream())
        #Save to file
        $stream.ReadToEnd() | Set-Content -Path $FilePath -Force 

    } catch [System.Net.WebException] {
        #Check for a 304
        if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::NotModified) {
            Write-Host "  $FilePath not modified, not downloading..."
            $error.clear()
        } else {
            #Unexpected error
            $Status = $_.Exception.Response.StatusCode
            $msg = $_.Exception
            Write-Host "  Error dowloading $FilePath, Status code: $Status - $msg"
        }
    }
}
}

function Get-HudlRoleAttributes {

    $role = Get-MyRole

    #reset values
    $environment = $environmentPrefix = $serverRole = $group = ""

    $roleSplit = $role -Split '-'
    if ($roleSplit.Length -eq 2) {
        # [0] - Environment Letter, [1] - server role
        $environmentPrefix = $roleSplit[0]
        $serverRole = $roleSplit[1]
        $group = "Monolith"
    } elseif ($roleSplit.Length -eq 3) {
        # [0] - Environment Letter, [1] - mvgroupmvgroup, [2] - server role
        $environmentPrefix = $roleSplit[0]
        $group = $roleSplit[1]
        $serverRole = $roleSplit[2]
    }
    # Special case for monolith web servers, they have a different format role name
    if ($serverRole -eq "role" -and $group -eq "web") {
        $serverRole = "Web"
        $group = "Monolith"
    }
    switch ($environmentPrefix) 
    {
        'p' { $environment = "prod" }
        's' { $environment = "stage" }
        'i' { $environment = "internal" }
        't' { $environment = "thor" }
    }
    $result = new-object psobject -Property @{
        EnvironmentPrefix = $environmentPrefix
        Environment = $environment
        ServerRole = $serverRole
        Group = $group
        IamRole = $role
    }
    return $result
}


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

$roleAttributes = Get-HudlRoleAttributes

# Set role tag if not set.
$chef_tag_role = Get-EC2Tag -Filters @( @{Name="key"; values="Role"}, @{Name="resource-id"; Values=$instanceId})
if ($chef_tag_role -eq $null) {
    Write-Output "Creating Role Tag"
    $tags = @()
    $tags = $tags + @{Key='Role'; Value="Role$($roleAttributes.ServerRole)"}
    New-EC2Tag -ResourceId $instanceid -Tag @tags
    $chef_tag_role = Get-EC2Tag -Filters @( @{Name="key"; values="Role"}, @{Name="resource-id"; Values=$instanceId})
}

# Set environment tag if not set.
$chef_tag_environment = Get-EC2Tag -Filters @( @{Name="key"; values="Environment"}, @{Name="resource-id"; Values=$instanceId})

if ($chef_tag_environment -eq $null) {
    Write-Output "Creating Environment Tag"
    $tags = @()
    $tags = $tags + @{Key='Environment'; Value="$($roleAttributes.Environment)"}
    New-EC2Tag -ResourceId $instanceid -Tag @tags
    $chef_tag_environment = Get-EC2Tag -Filters @( @{Name="key"; values="Environment"}, @{Name="resource-id"; Values=$instanceId})
}

# Set group tag if not set.
$chef_tag_group = Get-EC2Tag -Filters @( @{Name="key"; values="Group"}, @{Name="resource-id"; Values=$instanceId})
if ($chef_tag_group -eq $null) {
    Write-Output "Creating Group Tag"
    $tags = @()
    $tags = $tags + @{Key='Group'; Value="$($roleAttributes.Group)"}
    New-EC2Tag -ResourceId $instanceid -Tag @tags
    $chef_tag_group = Get-EC2Tag -Filters @( @{Name="key"; values="Group"}, @{Name="resource-id"; Values=$instanceId})
}

if ($roleAttributes.Environment -eq "prod") {
      $chef_environment = "prod"
} elseif ($roleAttributes.Environment -eq "stage") {
      $chef_environment = "stage"
} else {
      $chef_environment = "test"
}

if($chef_environment -eq "prod") {
  # Prod VPC proxy server
  $chef_server_url = 'http://ec2-107-21-20-8.compute-1.amazonaws.com/organizations/hudl'
} else {
  # EC2 classic proxy server
  $chef_server_url = 'http://ec2-54-234-253-166.compute-1.amazonaws.com/organizations/hudl'
}

# Check if in VPC to leave hint file for ec2 attributes in ohai
$hintsDir = "c:\chef\ohai\hints"
if( -not (Test-Path $hintsDir)) {
    Write-Output "Creating ohai hints directory"
    New-Item $hintsDir -type directory | Out-Null
}
$hintsFile = "$($hintsDir)\ec2.json"
if( -not (Test-Path $hintsFile)) {
    New-Item "c:\chef\ohai\hints\ec2.json" -type file
}

$eurekaSet = Get-Random -minimum 1 -maximum 3

# Install Chef
$windows_version = "2012r2"
$chef_version = "chef-client-12.6.0-1-x86.msi"
$server_name = $servername.Trim()
$chef_env = $chef_environment.ToLower().Trim()
$client_rb = @"
base_dir = "C:/Chef"
log_level        :info
log_location     STDOUT
chef_server_url  "$chef_server_url"
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

ohai.disabled_plugins= [
 "c", "cloud", "ec2", "rackspace", "eucalyptus", "command", "dmi", "dmi_common",
 "erlang", "groovy", "ip_scopes", "java", "keys", "lua", "mono", "network_listeners",
 "passwd", "perl", "php", "python", "ssh_host_key", "uptime", "virtualization",
 "windows::virtualization", "windows::kernel_devices"
 ]

"@

try { New-Item c:\temp -type directory } catch {}

# It doesn't appear the windows version matters as there is only one
# msi installer and it is listed for all types of Windows Server
try {
    $chefDownloadSource = "https://opscode-omnibus-packages.s3.amazonaws.com/windows/$windows_version/i386/$chef_version"
    $chefDownloadDestination = "c:\temp\chef-client.msi"
    Download-File $chefDownloadSource $chefDownloadDestination
    Write-Output "Chef Dowloaded, running installer."
    #Invoke-WebRequest $chefDownloadSource -OutFile $chefDownloadDestination 
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/qn /i c:\temp\chef-client.msi ADDLOCAL=`"ChefClientFeature,ChefServiceFeature,ChefPSModuleFeature`"" -Wait -NoNewWindow
    Write-Output "Chef Installed, downloading chef client config."
    Read-S3Object -BucketName "hudl-chef-artifacts" -KeyPrefix "chef-client" -Folder "c:\chef"
}
catch [Exception]{
    Write-Output "Failed to install Chef!" | Out-File -FilePath $USERDATA_LOG 
    Write-Output $_.Exception.Message | Out-File -FilePath $USERDATA_LOG -ErrorAction Stop
}

$format_client_rb = $client_rb -replace '[\u200B]+',''
$format_client_rb.Trim() | Out-File "c:\chef\client.rb" -Encoding utf8

# Run Chef with the Role from the AWS Tag
try {
    Write-Output "Starting saving Attributes step"
    $chef_role = "$($chef_tag_role.Value.ToLower())"

    # Save Attribute Data
    $attributeFile = "c:\chef\attributes.json"
    $attributesContent = @"
    {
      "hudl": {
        "environment": "$($roleAttributes.Environment)",
        "environmentPrefix": "$($roleAttributes.EnvironmentPrefix)",
        "iamRole": "$($roleAttributes.IamRole)",
        "serverRole": "$($roleAttributes.ServerRole)",
        "group": "$($roleAttributes.Group)",
        "service": "$($roleAttributes.Group)",
        "eureka_set": "$($eurekaSet)"
      }
    }
"@

    Write-Output "Beginning write to file"
    [System.IO.File]::WriteAllLines($attributeFile, $attributesContent)
    Write-Output "Chef attributes saved"
    $env:Path += ";C:\opscode\chef\bin"
    Write-Output "Starting Chef run."
    Start-Process -FilePath "chef-client" -ArgumentList "-c `"c:\chef\client.rb`" -r `"role[$chef_role]`" -L `"c:\chef\chef-client-initial-run.log`" -j `"c:\chef\attributes.json`"" -Wait -NoNewWindow
    Write-Output "Chef run started."
    }
catch [Exception]{
    Write-Output "Failed to run Chef!" | Out-File -FilePath $USERDATA_LOG 
    Write-Output "Failed to run chef"
    Write-Output $_.Exception.Message | Out-File -FilePath $USERDATA_LOG -ErrorAction Stop
    Write-Output $_.Exception.Message
}
</powershell>