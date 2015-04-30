import ec2
import s3
import elb
import route53

policies = {
    'allow-volume-control': ec2.allow_volume_control,
    'allow-describe-tags': ec2.allow_describe_tags,
    'allow-upload-to-s3-fulla': s3.allow_upload_to_s3_fulla,
    'allow-download-scripts-s3-fulla': s3.allow_download_scripts_s3_fulla,
    'allow-download-script-s3-stage-updater': s3.allow_download_script_s3_stage_updater,
    'allow-get-nginx-config': s3.allow_get_nginx_config,
    'allow-describe-elbs': elb.allow_describe_elbs,
    'allow-modify-nginx-elbs-stage': elb.allow_modify_nginx_elbs_stage,
    'allow-modify-nginx-elbs-prod': elb.allow_modify_nginx_elbs_prod,
    'allow-update-route53-stage': route53.allow_update_route53_stage,
    'allow-update-route53-prod': route53.allow_update_route53_prod
}
