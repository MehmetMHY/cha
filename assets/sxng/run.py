#!/usr/bin/env python3

import os
import sys
import subprocess
import yaml
import time
from pathlib import Path

# default values
DEFAULT_PORT = "8080"
DEFAULT_NAME = "searxng-search"
DEFAULT_URL = "http://localhost"


def check_docker():
    """check if docker is running"""
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not running. Please start Docker and try again.")
        return False


def get_user_input(prompt, default_value):
    """get user input with default value"""
    user_input = input(f"{prompt} (default {default_value}): ").strip()
    return user_input if user_input else default_value


def check_running_container(port):
    """check if a container is already running on the specified port"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def stop_container(container_id):
    """stop a running container"""
    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def update_searxng_image():
    """pull the latest searxng image"""
    try:
        print("Pulling latest searxng image...")
        subprocess.run(["docker", "pull", "searxng/searxng"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Warning: Failed to update SearXNG image")
        return False


def create_initial_config(port, name, base_url):
    """create initial searxng configuration by running container briefly"""
    try:
        print("Creating initial SearXNG configuration...")

        # get current directory for volume mount
        current_dir = os.getcwd()

        # run container to create initial config
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "-p",
                f"{port}:8080",
                "-v",
                f"{current_dir}/searxng:/etc/searxng",
                "-e",
                f"BASE_URL={base_url}:{port}/",
                "-e",
                f"INSTANCE_NAME={name}",
                "--name",
                f"{name}-init",
                "searxng/searxng",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        container_id = result.stdout.strip()

        # wait a few seconds for config to be created
        print("Waiting for configuration to be created...")
        time.sleep(5)

        # stop the container
        subprocess.run(["docker", "stop", container_id], check=True)

        # verify that settings.yml was created
        settings_file = Path("searxng/settings.yml")
        if settings_file.exists():
            print("Initial configuration created successfully")
            return True
        else:
            print("Error: Configuration file was not created")
            return False

    except subprocess.CalledProcessError as e:
        print("Error: Failed to create initial configuration")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def enable_json_format():
    """check and enable json format in settings.yml if needed"""
    settings_file = Path("searxng/settings.yml")

    if not settings_file.exists():
        print("Note: settings.yml not found. SearXNG will use default settings.")
        print("JSON format may not be available until you configure settings.yml")
        return False

    print("Checking SearXNG settings for JSON format support...")

    try:
        # load the yaml file
        with open(settings_file, "r") as file:
            settings = yaml.safe_load(file)

        # check if search section and formats exist
        if "search" not in settings:
            settings["search"] = {}

        if "formats" not in settings["search"]:
            settings["search"]["formats"] = ["html"]

        # check if json format is already enabled
        formats = settings["search"]["formats"]
        if "json" in formats:
            print("JSON format already enabled in settings.yml")
            return True

        # add json format
        print("Enabling JSON format in settings.yml...")
        formats.append("json")

        # create backup
        backup_file = settings_file.with_suffix(".yml.bak")
        if settings_file.exists():
            subprocess.run(["cp", str(settings_file), str(backup_file)], check=True)

        # write updated settings
        with open(settings_file, "w") as file:
            yaml.dump(settings, file, default_flow_style=False, sort_keys=False)

        print("Successfully enabled JSON format in settings.yml")
        return True

    except Exception as e:
        print(f"Warning: Could not automatically enable JSON format: {e}")
        print(
            "You may need to manually add 'json' to the formats section in settings.yml"
        )
        return False


def start_searxng_container(port, name, base_url):
    """start the searxng container"""
    try:
        print("Starting SearXNG container...")

        # get current directory for volume mount
        current_dir = os.getcwd()

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "-p",
                f"{port}:8080",
                "-v",
                f"{current_dir}/searxng:/etc/searxng",
                "-e",
                f"BASE_URL={base_url}:{port}/",
                "-e",
                f"INSTANCE_NAME={name}",
                "--name",
                name,
                "searxng/searxng",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        container_id = result.stdout.strip()
        print(f"SearXNG instance '{name}' is running on {base_url}:{port}")
        return True

    except subprocess.CalledProcessError as e:
        print(
            "Error: Failed to start SearXNG container. Please check Docker logs for more details."
        )
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def main():
    """main function"""
    # check if docker is running
    if not check_docker():
        sys.exit(1)

    # get user inputs
    port = get_user_input("Enter port", DEFAULT_PORT)
    name = get_user_input("Enter instance name", DEFAULT_NAME)
    base_url = get_user_input("Enter base URL", DEFAULT_URL)

    # check for running container on the same port
    running_container = check_running_container(port)
    if running_container:
        stop_choice = (
            input(f"An instance is already running on port {port}. Stop it? (y/n): ")
            .strip()
            .lower()
        )
        if stop_choice == "y":
            if not stop_container(running_container):
                print("Failed to stop the running container.")
                sys.exit(1)
        else:
            print("Exiting without changes.")
            sys.exit(0)

    # ask about updating the image
    update_choice = (
        input("Do you want to update the searxng image? (y/n): ").strip().lower()
    )
    if update_choice == "y":
        update_searxng_image()

    # check if searxng configuration directory exists
    searxng_dir = Path("searxng")
    settings_file = Path("searxng/settings.yml")

    if not searxng_dir.exists() or not settings_file.exists():
        print("SearXNG configuration not found. Creating initial configuration...")
        if not create_initial_config(port, name, base_url):
            print("Error: Failed to create initial configuration. Exiting.")
            sys.exit(1)

    # enable json format in settings
    enable_json_format()

    # start the container
    if start_searxng_container(port, name, base_url):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
