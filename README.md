  <h1 align="center">Streaming RTMP to Localhost using NGINX</h1>

  <p align="center">
    Proceduce by Tony Ngô & Thiện Nguyễn & Huy Nguyễn
    <br />
    <br />
    <a href="https://github.com/wordgod123/RTMPAddRes"><strong>Explore full origin source code »</strong></a>
    <br />
    <br />
    <a href="">View Demo</a>
    ·
    <a href="facebook.com/thinhngotony">Report Bug</a>
    ·
    <a href="facebook.com/thinhngotony">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project



### Built With

* [Python]()
* [Nginx]()
* [Docker]()


<!-- GETTING STARTED -->
## Getting Started

To run this code please do the following steps

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* All dependencies
  ```sh
  pip install -r requirements.txt
  ```

### Installation

1. Pull this [Nginx-RTMP](https://hub.docker.com/r/tiangolo/nginx-rtmp) on DockerHub
 
   Mark that the `url` in the code `main.py` is the file you want to streaming or you can change it to `0` to have a webcam streaming


<!-- USAGE EXAMPLES -->
## Usage

1. Run this command to run Nginx Server
  ```sh
  docker run -d -p 1935:1935 --name nginx-rtmp tiangolo/nginx-rtmp
  ```
2. Change the code in `main.py`
  ```sh
live = Live(inputUrl=url, rtmpUrl="rtmp://yourIP/live/")
with 'yourIP' is your server IP
  ```

3. Run the following command from terminal to streaming
  ```sh
  python main.py
  ```


<!-- ROADMAP -->
## Roadmap

Plan to change resolution in streaming soon!



<!-- CONTRIBUTING -->
## Contributing

You can pull requests and emails me for development 

<!-- LICENSE -->
## License

All of code is copied from lots of source in Github and Internet to remaster and optimized. This makes it will not be owned by any persons! Contact `Author - Tony` for more information.



<!-- CONTACT -->
## Contact

Your Name - [@thinhngotony](https://twitter.com/thinhngotony) - email - `thinhngotony@gmail.com`

More projects Link: [https://github.com/thinhngotony](https://github.com/thinhngotony)



