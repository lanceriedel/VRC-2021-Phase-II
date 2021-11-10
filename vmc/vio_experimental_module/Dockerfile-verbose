FROM stereolabs/zed:3.6-py-devel-jetson-jp4.6


ENV LIBREALSENSE_VERSION=v2.49.0
ENV DEBIAN_FRONTEND=noninteractive
# https://stackoverflow.com/a/66057286
ENV OPENBLAS_CORETYPE=ARMV8

# Needed as some repo certs are expired in the base image
RUN apt-get update -y || true \
 && apt-get install -y ca-certificates && update-ca-certificates
RUN apt update -y
RUN apt install -y \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    libusb-dev \
    usbutils \
    pkg-config \
    build-essential \
    cmake \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt update
RUN apt install -y \
    python3.8 \
    python3.8-distutils \
    python3.8-dev \
    python3-setuptools \
    python3-pip 

WORKDIR /


WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3.8 -m pip install pip wheel --upgrade && \
    python3.8 -m pip install -r requirements.txt
RUN ls -l /usr/local/
RUN ls -l /usr/local/zed #redo3
RUN ls -l /usr/local/zed/include
RUN ls -l /etc/

# ZED Python API
RUN wget download.stereolabs.com/zedsdk/pyzed -O /usr/local/zed/get_python_api.py
RUN python3.8 /usr/local/zed/get_python_api.py
    

RUN python3.8 -m pip install --ignore-installed /app/pyzed-3.6-cp38-cp38-linux_aarch64.whl

RUN curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | \
  sudo apt-key add - && \
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list &&  \
sudo apt-get update 
RUN apt-get install -y nvidia-container-runtime 

COPY . .

CMD ["python3.8", "vio-experimental.py"]
