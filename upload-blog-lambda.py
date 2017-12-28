import io
from io import BytesIO
import boto3
import zipfile
import mimetypes


def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-2:094608791377:deployBlog')

    try:
        build_bucket =  s3.Bucket('blogbuild.chrilliams.co.uk')
        blog_bucket = s3.Bucket('blog.chrilliams.co.uk')

        blog_zip = BytesIO()
        build_bucket.download_fileobj('blogbuild.zip', blog_zip)

        with zipfile.ZipFile(blog_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                blog_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                blog_bucket.Object(nm).Acl().put(ACL='public-read')

        topic.publish(Subject="Blog Deploy", Message="Blog Deployed Successfully")
    except:
        topic.publish(Subject="Blog Deploy Failed", Message="Blog was not deployed!")
        raise


    return 'Hello from Lambda'
