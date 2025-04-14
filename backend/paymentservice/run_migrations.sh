#!/bin/bash
check_and_create_env() {
    # Define the filenames
    local env_file=".env"
    local env_local_file=".env.local"
    
    # Check if the .env file exists
    if [ -f "$env_file" ]; then
        echo "$env_file already exists. Skipping creation."
    else
        # Check if .env.local exists
        if [ -f "$env_local_file" ]; then
            echo "$env_file not found. Creating $env_file from $env_local_file..."
            # Copy the content from .env.local to .env
            cp "$env_local_file" "$env_file"
            echo "Created $env_file from $env_local_file."
        else
            echo "$env_local_file does not exist. Please create the file and add your configuration."
        fi
    fi
}
# Call check_and_create_env function
check_and_create_env



