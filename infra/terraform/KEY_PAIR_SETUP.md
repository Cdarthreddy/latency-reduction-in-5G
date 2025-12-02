# EC2 Key Pair Setup

## Issue: Key Pair Not Found

If you see this error:
```
api error InvalidKeyPair.NotFound: The key pair 'project.pem' does not exist
```

You have two options:

## Option 1: Use an Existing Key Pair

1. List your existing key pairs:
```bash
aws ec2 describe-key-pairs --region us-east-1
```

2. Update `terraform.tfvars` with the correct key name:
```hcl
key_name = "your-existing-key-name"
```

## Option 2: Create a New Key Pair

### Via AWS Console:
1. Go to **EC2** → **Key Pairs**
2. Click **Create key pair**
3. Name: `project` (or any name you prefer)
4. Key pair type: **RSA**
5. Private key file format: **.pem** (for Linux/Mac) or **.ppk** (for Windows with PuTTY)
6. Click **Create key pair**
7. Save the downloaded `.pem` file securely

### Via AWS CLI:
```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name project \
  --query 'KeyMaterial' \
  --output text > project.pem

# Set proper permissions (Linux/Mac)
chmod 400 project.pem

# Update terraform.tfvars
key_name = "project"
```

## Option 3: Remove Key Pair Requirement (Not Recommended)

If you don't need SSH access and want to skip the key pair:

1. Update `terraform.tfvars`:
```hcl
key_name = ""  # Empty string - no key pair assigned
```

**Warning:** Without a key pair, you won't be able to SSH into the instance!

## Verify Key Pair

After creating or selecting a key pair:

```bash
# List key pairs
aws ec2 describe-key-pairs --region us-east-1

# Check if specific key exists
aws ec2 describe-key-pairs --key-names project --region us-east-1
```

## Using the Key Pair

After the EC2 instance is created, you can SSH into it:

```bash
# Linux/Mac
ssh -i project.pem ec2-user@<EC2_PUBLIC_IP>

# Windows (using PuTTY or WSL)
ssh -i project.pem ec2-user@<EC2_PUBLIC_IP>
```

## Troubleshooting

### Error: "Permission denied (publickey)"

Make sure:
1. Key pair name in Terraform matches the actual key pair name in AWS
2. You're using the correct private key file
3. Key file has correct permissions: `chmod 400 project.pem`

### Error: "Key pair already exists"

If you try to create a key pair that already exists, either:
- Use the existing one
- Delete the old one first (if you have the private key)

```bash
aws ec2 delete-key-pair --key-name project --region us-east-1
```

---

## Recommended Setup

For this project, it's recommended to:
1. Create a key pair named `project` or use an existing one
2. Keep the `.pem` file secure (don't commit it to git)
3. Add `.pem` files to `.gitignore`

