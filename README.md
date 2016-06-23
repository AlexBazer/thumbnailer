# thumbnailer

Simple nginx location setting:
```
    location /thumbnails/ {
        try_files $uri @django;
        alias <path to thumbnails media directory>/;
    }

```
