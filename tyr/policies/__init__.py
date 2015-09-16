import ec2
import s3
import elb
import route53

policies = {
    'allow-volume-control': ec2.allow_volume_control,
    'allow-describe-instances': ec2.allow_describe_instances,
    'allow-describe-tags': ec2.allow_describe_tags,
    'allow-create-tags': ec2.allow_create_tags,
    'allow-upload-to-s3-fulla': s3.allow_upload_to_s3_fulla,
    'allow-download-scripts-s3-fulla': s3.allow_download_scripts_s3_fulla,
    'allow-mongo-backup-snapshot': ec2.allow_mongo_backup_snapshot,
    'allow-mongo-snapshot-cleanup': ec2.allow_mongo_snapshot_cleanup,
    'allow-download-script-s3-stage-updater':
    s3.allow_download_script_s3_stage_updater,
    'allow-get-nginx-config': s3.allow_get_nginx_config,
    'allow-describe-elbs': elb.allow_describe_elbs,
    'allow-modify-nginx-elbs-test': None,
    'allow-modify-nginx-elbs-stage': elb.allow_modify_nginx_elbs_stage,
    'allow-modify-nginx-elbs-prod': elb.allow_modify_nginx_elbs_prod,
    'allow-outpost-sns-test': ec2.allow_outpost_sns_test,
    'allow-outpost-sns-stage': ec2.allow_outpost_sns_stage,
    'allow-outpost-sns-prod': ec2.allow_outpost_sns_prod,
    'allow-web-initialization-prod': ec2.allow_web_initialization_prod,
    'allow-web-initialization-stage': ec2.allow_web_initialization_stage,
    'allow-set-cloudwatch-alarms': ec2.allow_set_cloudwatch_alarms,
    'allow-remove-cloudwatch-alarms': ec2.allow_remove_cloudwatch_alarms,
    'allow-deploy-web-updates': ec2.allow_deploy_web_updates,
    'allow-get-solr-schema': s3.allow_get_solr_schema,
    'allow-describe-snapshots': ec2.allow_describe_snapshots,
    'allow-get-hudl-config': s3.allow_get_hudl_config,
    'allow-get-chef-artifacts-chef-client':
    s3.allow_get_chef_artifacts_chef_client,
    'allow-update-route53-test': None,
    'allow-update-route53-prod': route53.allow_update_route53_prod,
    'allow-update-route53-stage': route53.allow_update_route53_stage
}
