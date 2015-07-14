import ec2
import s3
import elb

policies = {
    'allow-volume-control': ec2.allow_volume_control,
    'allow-describe-instances': ec2.allow_describe_instances,
    'allow-describe-tags': ec2.allow_describe_tags,
    'allow-upload-to-s3-fulla': s3.allow_upload_to_s3_fulla,
    'allow-download-scripts-s3-fulla': s3.allow_download_scripts_s3_fulla,
    'allow-mongo-backup-snapshot': ec2.allow_mongo_backup_snapshot,
    'allow-mongo-snapshot-cleanup': ec2.allow_mongo_snapshot_cleanup,
    'allow-download-script-s3-stage-updater':
    s3.allow_download_script_s3_stage_updater,
    'allow-get-nginx-config': s3.allow_get_nginx_config,
    'allow-describe-elbs': elb.allow_describe_elbs,
    'allow-modify-nginx-elbs-stage': elb.allow_modify_nginx_elbs_stage,
    'allow-modify-nginx-elbs-prod': elb.allow_modify_nginx_elbs_prod,
    'allow-describe-snapshots': ec2.allow_describe_snapshots,
    'allow-get-hudl-config': s3.allow_get_hudl_config
}
