FROM python:3.10-bullseye
RUN pip install --upgrade pip
RUN pip install wheel
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user docker
COPY vps_status.py ./vps_status.py
CMD ["python", "vps_status.py"]