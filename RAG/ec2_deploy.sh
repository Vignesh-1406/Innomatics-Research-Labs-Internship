#!/bin/bash

AWS_REGION=${AWS_REGION:-us-east-1}
INSTANCE_TYPE=${INSTANCE_TYPE:-t3.medium}
KEY_NAME=${KEY_NAME:-bedrock-rag-key}
SECURITY_GROUP=${SECURITY_GROUP:-bedrock-rag-sg}
INSTANCE_NAME=${INSTANCE_NAME:-bedrock-rag-server}


create_key_pair() {
    echo "Creating EC2 key pair: $KEY_NAME"
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $AWS_REGION \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    
    chmod 400 ${KEY_NAME}.pem
    echo "Key pair saved to ${KEY_NAME}.pem"
}


create_security_group() {
    echo "Creating security group: $SECURITY_GROUP"
    
    vpc_id=$(aws ec2 describe-vpcs \
        --region $AWS_REGION \
        --query 'Vpcs[0].VpcId' \
        --output text)
    
    aws ec2 create-security-group \
        --group-name $SECURITY_GROUP \
        --description "Security group for Bedrock RAG" \
        --vpc-id $vpc_id \
        --region $AWS_REGION
    
    sg_id=$(aws ec2 describe-security-groups \
        --filters Name=group-name,Values=$SECURITY_GROUP \
        --region $AWS_REGION \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    aws ec2 authorize-security-group-ingress \
        --group-id $sg_id \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-id $sg_id \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-id $sg_id \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
    
    echo "Security group created: $sg_id"
}


create_iam_instance_profile() {
    echo "Creating IAM instance profile"
    
    assume_role_policy='{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "ec2.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }'
    
    aws iam create-role \
        --role-name BedrockEC2Role \
        --assume-role-policy-document "$assume_role_policy" 2>/dev/null || echo "Role already exists"
    
    aws iam attach-role-policy \
        --role-name BedrockEC2Role \
        --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || echo "Policy already attached"
    
    aws iam create-instance-profile \
        --instance-profile-name BedrockEC2Profile 2>/dev/null || echo "Instance profile already exists"
    
    aws iam add-role-to-instance-profile \
        --instance-profile-name BedrockEC2Profile \
        --role-name BedrockEC2Role 2>/dev/null || echo "Role already added to profile"
    
    echo "IAM instance profile created"
}


launch_instance() {
    echo "Launching EC2 instance..."
    
    sg_id=$(aws ec2 describe-security-groups \
        --filters Name=group-name,Values=$SECURITY_GROUP \
        --region $AWS_REGION \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    user_data_script='#!/bin/bash
    yum update -y
    yum install -y python3 python3-pip git
    
    cd /opt
    git clone https://github.com/yourusername/bedrock-rag.git
    cd bedrock-rag
    
    pip3 install -r bedrock_requirements.txt
    
    export AWS_REGION=us-east-1
    
    nohup streamlit run bedrock_streamlit_app.py --server.port 8501 &
    '
    
    instance_id=$(aws ec2 run-instances \
        --image-id ami-0885b1f6bd170450c \
        --instance-type $INSTANCE_TYPE \
        --key-name $KEY_NAME \
        --security-group-ids $sg_id \
        --iam-instance-profile Name=BedrockEC2Profile \
        --region $AWS_REGION \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
        --user-data "$user_data_script" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    echo "Instance launched: $instance_id"
    echo "Waiting for instance to start..."
    
    aws ec2 wait instance-running \
        --instance-ids $instance_id \
        --region $AWS_REGION
    
    public_ip=$(aws ec2 describe-instances \
        --instance-ids $instance_id \
        --region $AWS_REGION \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    echo "\n=========================================="
    echo "EC2 Instance Details"
    echo "=========================================="
    echo "Instance ID: $instance_id"
    echo "Public IP: $public_ip"
    echo "SSH Command: ssh -i ${KEY_NAME}.pem ec2-user@$public_ip"
    echo "Streamlit URL: http://$public_ip:8501"
    echo "=========================================="
}


cleanup() {
    echo "Cleaning up resources..."
    
    instances=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$INSTANCE_NAME" \
        --region $AWS_REGION \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text)
    
    if [ ! -z "$instances" ]; then
        aws ec2 terminate-instances \
            --instance-ids $instances \
            --region $AWS_REGION
        echo "Instances terminated"
    fi
    
    sg_id=$(aws ec2 describe-security-groups \
        --filters Name=group-name,Values=$SECURITY_GROUP \
        --region $AWS_REGION \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)
    
    if [ ! -z "$sg_id" ] && [ "$sg_id" != "None" ]; then
        sleep 30
        aws ec2 delete-security-group \
            --group-id $sg_id \
            --region $AWS_REGION 2>/dev/null || echo "Could not delete security group"
    fi
    
    if [ -f "${KEY_NAME}.pem" ]; then
        rm ${KEY_NAME}.pem
        echo "Key pair deleted locally"
    fi
}


main() {
    case ${1:-deploy} in
    deploy)
        create_key_pair
        create_security_group
        create_iam_instance_profile
        launch_instance
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup}"
        exit 1
        ;;
    esac
}

main $@
