
# 使用標準且穩定的 Python slim 映像檔 (基於 Debian Bookworm, Debian 12)
FROM python:3.12-slim

# 設定環境變數，啟用非互動模式
ENV DEBIAN_FRONTEND=noninteractive

# 安裝必要的工具：curl, gnupg, 以及 Google Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    gnupg

# 匯入 Google Cloud GPG 金鑰
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

# 將 Google Cloud SDK 儲存庫加入 APT 來源清單
RUN echo "deb https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# 再次更新並安裝 Google Cloud SDK
RUN apt-get update && apt-get install -y google-cloud-sdk

# 設定工作目錄
WORKDIR /workspaces/vibe-poetry
