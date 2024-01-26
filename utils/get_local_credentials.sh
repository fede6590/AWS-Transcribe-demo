function credentials_parser() {
  credentials_path="$1"

  # Convert Windows path to Unix path
  credentials_path="${credentials_path//\\//}"

  if [[ ! -f "$credentials_path" ]]; then
    echo "Error: Credentials file not found: $credentials_path" >&2
    return 1
  fi

  IFS=$'\n' read -r -d '' -a lines < "$credentials_path"

  aws_access_key_id="${lines[1]#*=}"  # Extract value after "="
  aws_secret_access_key="${lines[2]#*=}"

  aws_access_key_id="${aws_access_key_id//[$'\t\r\n ']}"  # Remove whitespace
  aws_secret_access_key="${aws_secret_access_key//[$'\t\r\n ']}"

  export AWS_ACCESS_KEY_ID="${aws_access_key_id^^}"  # Set as uppercase env var
  export AWS_SECRET_ACCESS_KEY="${aws_secret_access_key^^}"

  echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}"
  echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}"
}

credentials_parser "/mnt/c/Users/u633714/.aws/credentials"
