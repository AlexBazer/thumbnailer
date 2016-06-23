# thumbnailer

Simple nginx location setting:
```
    location /thumbnails/ {
        try_files $uri @django;
        alias /home/user/filmoved/media/thumbnails/;
    }

```
