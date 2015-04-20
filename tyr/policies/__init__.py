import ec2
import s3

policies = {
    'allow-volume-control': ec2.allow_volume_control,
    'allow-upload-to-s3-fulla': s3.allow_upload_to_s3_fulla,
    'allow-download-scripts-s3-fulla': s3.allow_download_scripts_s3_fulla,
    'allow-mongo-backup-snapshot': ec2.allow_mongo_backup_snapshot,
    'allow-mongo-snapshot-cleanup': ec2.allow_mongo_snapshot_cleanup
}
