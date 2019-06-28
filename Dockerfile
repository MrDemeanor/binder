FROM ubuntu:latest
MAINTAINER Brent Redmon "btr26@txstate.edu"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /binder
WORKDIR /binder
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["main.py"]