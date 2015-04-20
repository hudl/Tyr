import ec2
import s3

policies = {
    'allow-volume-control': ec2.allow_volume_control,
    'allow-upload-to-s3-fulla': s3.allow_upload_to_s3_fulla,
    'allow-download-scripts-s3-fulla': s3.allow_download_scripts_s3_fulla,
    'allow-download-script-s3-stage-updater': s3.allow_download_script_s3_stage_updater
}
