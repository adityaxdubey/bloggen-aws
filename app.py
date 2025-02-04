import boto3
import json
from datetime import datetime

#here i have initilised boto handler
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def generate_blog_with_bedrock(blog_topic: str) -> str:
    prompt = f"""<s>[INST]Human: Write a 200-word blog on the topic: {blog_topic}
    Assistant:[/INST]
    """

    body = json.dumps({
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0.5,
        "top_p": 0.9
    })

    try:
        #setting the modell
        response = bedrock.invoke_model(
            body=body,
            modelId="meta.llama3-8b-instruct-v1:0",
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('generation', '')
    except Exception as e:
        print(f"An error occurred while generating the blog: {e}")
        return ""

def save_to_s3(content: str, bucket_name: str, key: str):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=content)
        print(f"Blog content saved to S3: s3://{bucket_name}/{key}")
    except Exception as e:
        print(f"Failed to save to S3: {e}")

def lambda_handler(event, context):
    #this works for json
    body = json.loads(event['body'])
    topic = body.get('blog_topic', 'No Topic Provided')

    generated_blog = generate_blog_with_bedrock(topic)
    
    if generated_blog:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"blog-output/{current_time}.txt"
        s3_bucket = 'awsbedrockllm'  #bucket name which i kept

        save_to_s3(generated_blog, s3_bucket, s3_key)
        status_message = f"Blog generated and saved for topic: {topic}"
    else:
        status_message = "Failed to generate blog content."

    return {
        'statusCode': 200,
        'body': json.dumps(status_message)
    }