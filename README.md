# oscilok
Processing data from oscilloscope


## Oscilloscope setup
1. Square wave 5 V/DIV
2. Sine wave 2 V/DIV
3. Time 400 us/DIV


## Window setup
We use old machine to run the program with oscilloscope. So it is Windows 7 32 bits :D

To run the program, we gonna use old python 3.7.6 to make sure that all windows 7 machines can run it.

Let's start with [Python 3.7.6](https://www.python.org/ftp/python/3.7.6/python-3.7.6.exe). After installation on the new fresh Win7 machine I got the error "The program can't start because api-ms-win-crt-runtime-l1-1-0.dll is missing". Then we have to install [Visual C++ Redistributable for Visual Studio 2015 (32-bit)](https://www.microsoft.com/en-us/download/details.aspx?id=48145) and you will get the python on Command Prompt.
![Setup python on windows 7](https://raw.githubusercontent.com/qoopooh/oscilok/main/img/python376-on-win7.png)

### Oscilloscope driver
We test with [Hantek MSO5102D](http://www.hantek.com/products/detail/10), you can download driver from [official website](http://www.hantek.com/Product/MSO5000D/MSO5000D_Driver.zip).

For python, please install [libusb-win32-devel-filter-1.2.6.0.exe](https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/libusb-win32-devel-filter-1.2.6.0.exe/download)


## Linux setup
You have to copy file 50-myusb.rules to ```/etc/udev/rules.d/```. After that please reload the rules.
> sudo udevadm control -R

### Create app icon
Modify path of this project in oscilok.desktop and run the command below:
> desktop-file-install --dir=$HOME/.local/share/applications oscilok.desktop

### Build binary
> pyinstaller --onefile --noconfirm --noconsole --exclude-module _bootlocale --name oscilok src/main.pyw
