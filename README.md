![oscilok_logo](https://github.com/qoopooh/oscilok/blob/main/img/oscilok_logo.png?raw=true)
# oscilok
Processing data from oscilloscope


## Criteria
We will test the wire harness (DUT) and measuring 2 signals:
* Sine Wave
* Square Wave

The signals should have positive amplitude at the same time, otherwise test result will be failed.

<img src="https://github.com/qoopooh/oscilok/blob/main/img/ok.png?raw=true" alt="OK" width="360"/>

OK: Both have peaks in the same direction.


<img src="https://github.com/qoopooh/oscilok/blob/main/img/ng-opposite.png?raw=true" alt="ng opposite" width="360"/>

NG: One is positive amplitude, the other is negative


## Oscilloscope setup
<img src="https://github.com/qoopooh/oscilok/blob/main/img/16572956068466.jpg?raw=true" alt="ng single" width="300"/>

1. Square wave 5 V/DIV
2. Sine wave 2 V/DIV
3. Time 400 us/DIV

-----

## Window setup
We use old machine to run the program with oscilloscope. So it is Windows 7 32 bits :D

To run the program, we gonna use old python 3.7.6 to make sure that all windows 7 machines can run it.

Let's start with [Python 3.7.6](https://www.python.org/ftp/python/3.7.6/python-3.7.6.exe) (or [64 bits](https://www.python.org/ftp/python/3.7.6/python-3.7.6-amd64.exe)). After installation on the new fresh Win7 machine I got the error "The program can't start because api-ms-win-crt-runtime-l1-1-0.dll is missing". Then we have to install [Visual C++ Redistributable for Visual Studio 2015 (32-bit)](https://www.microsoft.com/en-us/download/details.aspx?id=48145) and you will get the python on Command Prompt.
<img src="https://raw.githubusercontent.com/qoopooh/oscilok/main/img/python376-on-win7.png" alt="Setup python on windows 7" width="360"/>

### Oscilloscope driver
~~We test with [Hantek MSO5102D](http://www.hantek.com/products/detail/10), you can download driver from [official website](http://www.hantek.com/Product/MSO5000D/MSO5000D_Driver.zip)~~.

~~For python, please install [libusb-win32-devel-filter-1.2.6.0.exe](https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/libusb-win32-devel-filter-1.2.6.0.exe/download)~~

Use [Zadig](https://zadig.akeo.ie/) and select [libusb-win32](https://sourceforge.net/p/libusb-win32/wiki/Home/)

### Build binary
TODO: Still cannot debug error after build
> pyinstaller --onefile --noconfirm --noconsole --icon=img\favicon.ico --exclude-module _bootlocale --name oscilok src\main.pyw

-----

## Linux setup
The new python 3.10 does not include tkinter, we have addtional for install GUI toolkit.
> sudo apt install python3-tk

You have to copy file 50-myusb.rules to ```/etc/udev/rules.d/```. After that please reload the rules.
```sh
sudo udevadm control -R
sudo udevadm trigger
```

Current user should be a member in ```plugdev``` group to access the USB device, if not please run the commands below:
```sh
sudo adduser $USER plugdev
newgrp plugdev # reload plugdev group
```

### Create app icon
Modify path of this project in oscilok.desktop and run the command below:
> desktop-file-install --dir=$HOME/.local/share/applications oscilok.desktop

### Build binary
> pyinstaller --onefile --noconfirm --noconsole --exclude-module _bootlocale --name oscilok src/main.pyw
