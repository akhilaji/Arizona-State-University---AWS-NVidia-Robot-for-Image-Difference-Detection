FROM nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04

# prevent prompt from asking for timezone
ENV TZ=US/Arizona
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install essentials
RUN apt-get update && apt-get install -y \
        build-essential \
        libssl-dev \
        libgtk2.0-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libopencv-dev \
        pkg-config \
        wget \
        unzip \
        git

# install python
RUN apt-get update && apt-get install -y \
        python-dev \
        python-pip \
        python3-dev \
        python3-pip \
        python-numpy \
        python-pycurl \
        python-opencv

# upgrade pip
RUN pip3 install --upgrade pip

# install python3 pip packages
RUN pip3 install \
        tensorflow \
        torch \
        torchvision \
        opencv-python

# creates workspace directory to act as a root for this project
RUN mkdir workspace && cd workspace && \
        mkdir git && \
        mkdir models

#install cmake
RUN cd workspace/git && \
        wget https://github.com/Kitware/CMake/releases/download/v3.16.5/cmake-3.16.5.tar.gz && \
        tar -zxvf cmake-3.16.5.tar.gz && rm cmake-3.16.5.tar.gz && \
        cd cmake-3.16.5 && sh bootstrap && \
        make -j"$(nproc)" && make install

# install opencv
RUN git clone https://github.com/opencv/opencv.git workspace/git/opencv
RUN cd workspace/git/opencv && mkdir build && cd build && \
        cmake .. && make -j"$(nproc)" && make install

# install darknet
RUN git clone https://github.com/pjreddie/darknet.git workspace/git/darknet
RUN cd workspace/git/darknet && \
        sed -i 's/GPU=0/GPU=1/' Makefile && \
        sed -i 's/CUDNN=0/CUDNN=1/' Makefile && \
        sed -i 's/OPENCV=0/OPENCV=1/' Makefile && \
        make -j"$(nproc)"

# install MiDaS
RUN git clone https://github.com/intel-isl/MiDaS.git workspace/git/MiDaS && \
        cd workspace/models && \
        wget https://github.com/intel-isl/MiDaS/releases/download/v2/model-f46da743.pt  && \
        mv model-f46da743.pt intel-isl_MiDaS_v2_model-f46da743.pt
RUN cd root/.cache && \
        wget https://github.com/facebookresearch/WSL-Images/archive/master.zip && \
        unzip master.zip && rm master.zip && \
        mkdir hub && cd hub && \
        mkdir checkpoints && cd checkpoints && \
        wget https://download.pytorch.org/models/ig_resnext101_32x8-c38310e5.pth

#Downloading: "https://github.com/facebookresearch/WSL-Images/archive/master.zip" to /root/.cache/torch/hub/master.zip
#Downloading: "https://download.pytorch.org/models/ig_resnext101_32x8-c38310e5.pth" to /root/.cache/torch/hub/checkpoints/ig_resnext101_32x8-c38310e5.pth

# install project repository
RUN git clone https://github.com/akhilaji/aws-nvidia-robot-capstone workspace/git/aws-nvidia-robot-capstone

# setup envrionment variables
RUN echo 'alias MiDaS="python3 /workspace/git/aws-nvidia-robot-capstone/scripts/midas_wrapper.py"' >> ~/.bashrc
RUN echo 'alias split="python3 /workspace/git/aws-nvidia-robot-capstone/scripts/split.py"' >> ~/.bashrc
RUN echo 'alias encode="python3 /workspace/git/aws-nvidia-robot-capstone/scripts/encode.py"' >> ~/.bashrc
