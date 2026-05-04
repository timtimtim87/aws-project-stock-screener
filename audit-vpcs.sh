#!/bin/bash

# VPC Audit Script
# This script checks all AWS regions for VPCs and their resources
# Helps identify which VPCs are safe to delete

echo "=========================================="
echo "AWS VPC Audit Script"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI not configured or credentials invalid"
    echo "Run 'aws configure' first"
    exit 1
fi

echo "✓ AWS CLI configured"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"
echo ""

# Get all enabled regions
echo "Fetching enabled regions..."
REGIONS=$(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text)
echo "✓ Found $(echo $REGIONS | wc -w) regions"
echo ""

# Initialize counters
TOTAL_VPCS=0
EMPTY_VPCS=0
OCCUPIED_VPCS=0

# Array to store results
declare -a SAFE_TO_DELETE
declare -a KEEP_THESE

echo "=========================================="
echo "Scanning VPCs in all regions..."
echo "=========================================="
echo ""

for REGION in $REGIONS; do
    echo "Region: $REGION"
    echo "---"
    
    # Get all VPCs in this region
    VPCS=$(aws ec2 describe-vpcs --region $REGION --query 'Vpcs[*].[VpcId,IsDefault,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output text 2>/dev/null)
    
    if [ -z "$VPCS" ]; then
        echo "  No VPCs found"
        echo ""
        continue
    fi
    
    # Process each VPC
    while IFS=$'\t' read -r VPC_ID IS_DEFAULT CIDR NAME; do
        TOTAL_VPCS=$((TOTAL_VPCS + 1))
        
        # Handle empty name
        if [ "$NAME" == "None" ] || [ -z "$NAME" ]; then
            NAME="(unnamed)"
        fi
        
        # Default VPC indicator
        if [ "$IS_DEFAULT" == "True" ]; then
            DEFAULT_TAG="[DEFAULT]"
        else
            DEFAULT_TAG=""
        fi
        
        echo "  VPC: $VPC_ID $DEFAULT_TAG"
        echo "  Name: $NAME"
        echo "  CIDR: $CIDR"
        
        # Check for resources in this VPC
        HAS_RESOURCES=false
        RESOURCE_LIST=""
        
        # Check EC2 instances
        INSTANCES=$(aws ec2 describe-instances \
            --region $REGION \
            --filters "Name=vpc-id,Values=$VPC_ID" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
            --query 'Reservations[*].Instances[*].InstanceId' \
            --output text 2>/dev/null)
        
        if [ ! -z "$INSTANCES" ]; then
            INSTANCE_COUNT=$(echo $INSTANCES | wc -w)
            HAS_RESOURCES=true
            RESOURCE_LIST="$RESOURCE_LIST    • $INSTANCE_COUNT EC2 instance(s)\n"
        fi
        
        # Check NAT Gateways (these cost money!)
        NAT_GWS=$(aws ec2 describe-nat-gateways \
            --region $REGION \
            --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available" \
            --query 'NatGateways[*].NatGatewayId' \
            --output text 2>/dev/null)
        
        if [ ! -z "$NAT_GWS" ]; then
            NAT_COUNT=$(echo $NAT_GWS | wc -w)
            HAS_RESOURCES=true
            RESOURCE_LIST="$RESOURCE_LIST    • $NAT_COUNT NAT Gateway(s) (COSTS MONEY)\n"
        fi
        
        # Check RDS instances
        RDS_DBS=$(aws rds describe-db-instances \
            --region $REGION \
            --query "DBInstances[?DBSubnetGroup.VpcId=='$VPC_ID'].DBInstanceIdentifier" \
            --output text 2>/dev/null)
        
        if [ ! -z "$RDS_DBS" ]; then
            RDS_COUNT=$(echo $RDS_DBS | wc -w)
            HAS_RESOURCES=true
            RESOURCE_LIST="$RESOURCE_LIST    • $RDS_COUNT RDS database(s)\n"
        fi
        
        # Check Load Balancers
        LBS=$(aws elbv2 describe-load-balancers \
            --region $REGION \
            --query "LoadBalancers[?VpcId=='$VPC_ID'].LoadBalancerArn" \
            --output text 2>/dev/null)
        
        if [ ! -z "$LBS" ]; then
            LB_COUNT=$(echo $LBS | wc -w)
            HAS_RESOURCES=true
            RESOURCE_LIST="$RESOURCE_LIST    • $LB_COUNT Load Balancer(s)\n"
        fi
        
        # Check Lambda functions in VPC
        LAMBDAS=$(aws lambda list-functions \
            --region $REGION \
            --query "Functions[?VpcConfig.VpcId=='$VPC_ID'].FunctionName" \
            --output text 2>/dev/null)
        
        if [ ! -z "$LAMBDAS" ]; then
            LAMBDA_COUNT=$(echo $LAMBDAS | wc -w)
            HAS_RESOURCES=true
            RESOURCE_LIST="$RESOURCE_LIST    • $LAMBDA_COUNT Lambda function(s)\n"
        fi
        
        # Display results
        if [ "$HAS_RESOURCES" = true ]; then
            echo "  Status: HAS RESOURCES - KEEP THIS"
            echo -e "$RESOURCE_LIST"
            OCCUPIED_VPCS=$((OCCUPIED_VPCS + 1))
            KEEP_THESE+=("$REGION: $VPC_ID ($NAME) $DEFAULT_TAG")
        else
            echo "  Status: ✓ EMPTY - Safe to delete"
            EMPTY_VPCS=$((EMPTY_VPCS + 1))
            SAFE_TO_DELETE+=("$REGION: $VPC_ID ($NAME) $DEFAULT_TAG")
        fi
        
        echo ""
        
    done <<< "$VPCS"
    
done

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "Total VPCs found: $TOTAL_VPCS"
echo "VPCs with resources (KEEP): $OCCUPIED_VPCS"
echo "Empty VPCs (safe to delete): $EMPTY_VPCS"
echo ""

if [ $OCCUPIED_VPCS -gt 0 ]; then
    echo "---"
    echo "VPCs to KEEP (have resources):"
    echo "---"
    for vpc in "${KEEP_THESE[@]}"; do
        echo "  • $vpc"
    done
    echo ""
fi

if [ $EMPTY_VPCS -gt 0 ]; then
    echo "---"
    echo "✓ VPCs safe to DELETE (empty):"
    echo "---"
    for vpc in "${SAFE_TO_DELETE[@]}"; do
        echo "  • $vpc"
    done
    echo ""
    echo "To delete a VPC, use:"
    echo "  aws ec2 delete-vpc --vpc-id vpc-xxxxx --region REGION"
    echo ""
    echo "Note: Default VPCs can be deleted but AWS recreates them easily."
    echo "   Most people keep default VPCs unless they have a specific reason."
else
    echo "✓ No empty VPCs found - all VPCs are in use!"
fi

echo ""
echo "=========================================="
echo "Audit complete!"
echo "=========================================="