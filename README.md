# oscilok
Processing data from oscilloscope


## Window setup
We use old machine to run the program with oscilloscope. So it is Windows 7 32 bits :D

To run the program, we gonna use old python 3.7.6 to make sure that all windows 7 machines can run it.

Let's start with [Python 3.7.6](https://www.python.org/ftp/python/3.7.6/python-3.7.6.exe). After installation on the new fresh Win7 machine I got the error "The program can't start because api-ms-win-crt-runtime-l1-1-0.dll is missing". Then we have to install [Visual C++ Redistributable for Visual Studio 2015 (32-bit)](https://www.microsoft.com/en-us/download/details.aspx?id=48145) and you will get the python on Command Prompt.

Python does not include pip like Linux/MacOS. Please [get pip here](https://pip.pypa.io/en/stable/installation/#get-pip-py).

### Oscilloscop driver
We test with [Hantek MSO5102D](http://www.hantek.com/products/detail/10), you can download driver from [official website](http://www.hantek.com/Product/MSO5000D/MSO5000D_Driver.zip).
