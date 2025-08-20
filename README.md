# Enhanced VideoMerge-Bot

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Telegram](https://img.shields.io/badge/Developer-@AbirHasan2005-blue?style=for-the-badge&logo=telegram)](https://t.me/AbirHasan2005)

An advanced, feature-rich Telegram bot that merges multiple videos from both direct uploads and URLs, with support for dual platform uploads to Telegram and GoFile.io. Built for performance, reliability, and easy deployment.

---

## ✨ Key Features

| Feature                  | Description                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| **Direct URL Support**   | Download videos directly from URLs (e.g., `.mp4`, `.mkv`) and add them to the merge queue.                |
| **GoFile.io Integration**| Upload merged videos to GoFile.io for permanent links and to bypass Telegram's file size limits.        |
| **Dual Platform Upload** | Uploads the final video to both Telegram and GoFile.io simultaneously, providing multiple download options. |
| **Docker Ready**         | Includes a production-ready `Dockerfile` and `docker-compose.yml` for easy, isolated deployment.      |
| **Async Performance**    | Built with `asyncio` for high-performance, non-blocking operations to handle multiple users efficiently. |
| **Enhanced Progress**    | Real-time progress updates for both downloading and uploading, keeping the user informed.                 |
| **Auto Cleanup**         | Automatically cleans up temporary files and directories to save disk space.                               |
| **Original Features**    | Retains all core features like custom thumbnails, broadcasting, and user settings.                      |

---

## 🚀 Deployment

### **1. Docker Deployment (Recommended)**

Deploying with Docker is the easiest and most reliable method.

**Prerequisites:**
*   Docker & Docker Compose installed.

**Steps:**
1.  **Clone the repository:**
    ```
    git clone https://github.com/YourUsername/VideoMerge-Bot-Enhanced.git
    cd VideoMerge-Bot-Enhanced
    ```

2.  **Create the configuration file:**
    Copy the example environment file and fill it with your credentials.
    ```
    cp .env.example .env
    nano .env
    ```

3.  **Build and run the container:**
    This command will build the Docker image and start the bot in the background.
    ```
    docker-compose up -d --build
    ```

4.  **Check the logs:**
    To see the bot's output and ensure it's running correctly:
    ```
    docker-compose logs -f
    ```

---

### **2. Manual VPS Deployment**

**Prerequisites:**
*   Ubuntu 20.04+
*   Python 3.9+
*   FFmpeg

**Steps:**
1.  **Install system dependencies:**
    ```
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3 python3-pip ffmpeg git -y
    ```
2.  **Clone the repository and install packages:**
    ```
    git clone https://github.com/YourUsername/VideoMerge-Bot-Enhanced.git
    cd VideoMerge-Bot-Enhanced
    pip3 install -r requirements.txt
    ```
3.  **Configure the bot:**
    ```
    cp .env.example .env
    nano .env
    ```
4.  **Run the bot:**
    ```
    python3 main.py
    ```

---

## ⚙️ Configuration

Create a `.env` file in the root directory and add the following variables:

| Variable                  | Description                                            | Required |
| ------------------------- | ------------------------------------------------------ | -------- |
| `API_ID`                  | Your Telegram API ID from `my.telegram.org`.           | **Yes**  |
| `API_HASH`                | Your Telegram API Hash from `my.telegram.org`.         | **Yes**  |
| `BOT_TOKEN`               | The token for your bot from `@BotFather`.              | **Yes**  |
| `BOT_OWNER`               | Your numeric Telegram User ID.                         | **Yes**  |
| `MONGODB_URI`             | Your MongoDB connection string.                        | **Yes**  |
| `UPDATES_CHANNEL`         | ID of a channel for Force Subscription (optional).     | No       |
| `LOG_CHANNEL`             | ID of a channel for logging bot activities (optional). | No       |
| `GOFILE_API_TOKEN`        | Your GoFile.io API token (optional).                   | No       |
| `MAX_VIDEOS`              | Max videos allowed in the merge queue (default: `5`).  | No       |
| `MAX_DOWNLOAD_SIZE`       | Max download size in bytes (default: `2147483648`).   | No       |

---

## 📖 How to Use

1.  **Start the Bot**: Send `/start` to initialize the bot.
2.  **Send Videos**:
    *   **Upload a file**: Send a video directly to the bot.
    *   **Send a URL**: Paste a direct download link to a video file.
3.  **Manage Queue**: Add up to the configured `MAX_VIDEOS` limit. Use `/clear` to reset the queue.
4.  **Merge**: Send the `/merge` command.
5.  **Download**: The bot will reply with download links for both Telegram and GoFile.io.

---

## 🏗️ Architecture

The project is built with a modular and scalable architecture:
*   `main.py`: The main application entry point that handles bot commands and user interactions.
*   `configs.py`: Centralized configuration management.
*   `helpers/`: A directory containing all the core logic modules:
    *   `downloader.py`: Handles downloading videos from URLs.
    *   `gofile_uploader.py`: Manages uploads to GoFile.io.
    *   `uploader.py`: Orchestrates the dual upload process.
    *   `merger.py`: Contains the FFmpeg logic for merging videos.
    *   `clean.py`: Manages the cleanup of temporary files.
    *   `database/`: Handles all interactions with the MongoDB database.

---

## 🙏 Acknowledgments

*   **Original Author**: This project is an enhanced version of the original [VideoMerge-Bot](https://github.com/AbirHasan2005/VideoMerge-Bot) by **@AbirHasan2005**.
*   **Libraries**: A huge thanks to the developers of [Pyrogram](https://pyrogram.org/) and [FFmpeg](https://ffmpeg.org/).

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```
