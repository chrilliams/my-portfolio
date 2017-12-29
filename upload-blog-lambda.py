import io
from io import BytesIO
import boto3
import zipfile
import mimetypes


def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-2:094608791377:deployBlog')
    codepipline = boto3.client('codepipeline')

    location = {
        "bucketName": "blogbuild.chrilliams.co.uk",
        "objectKey": "blogbuild.zip"
    }
    job = event.get("CodePipeline.job")

    try:
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print("Building Blog from " + str(location))

        build_bucket = s3.Bucket(location["bucketName"])
        blog_bucket = s3.Bucket('blog.chrilliams.co.uk')

        blog_zip = BytesIO()
        build_bucket.download_fileobj(location["objectKey"], blog_zip)

        with zipfile.ZipFile(blog_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                blog_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                blog_bucket.Object(nm).Acl().put(ACL='public-read')

        topic.publish(Subject="Blog Deploy", Message="Blog Deployed Successfully")
        if job:
            codepipline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="Blog Deploy Failed", Message="Blog was not deployed!")
        if job:
            codepipline.put_job_failure_result(jobId=job["id"],
                failureDetails={
                    'type': 'JobFailed',
                    'message': 'Blog was not deployed'})
        raise


    return 'Hello from Lambda'
