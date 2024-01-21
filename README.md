# PyFiche

PyFiche is a simple pastebin optimized for the command line, written in Python
and heavily inspired by [fiche](https://github.com/solusipse/fiche/), or rather
a shameless translation.

It also comes with a re-implementation of Lines, the HTTP server that comes
with Fiche, which this time allows you to upload files, and comes doesn't have
dependencies outside the standard library. Additionally, PyFiche also comes 
with a simple TCP server, Recup, to download pastes through netcat without 
using HTTP(S), in the same way you upload them.

## Installation

### Dependencies

* Python 3 (tested with 3.11)

### Local Installation

```bash
$ python -m venv venv
$ source venv/bin/activate
$ pip install -U git+https://kumig.it/PrivateCoffee/pyfiche.git
```

## Usage

### Fiche Server

```bash
$ source venv/bin/activate
$ pyfiche-server # try --help for options
```

With the exception of the `-u` option, all arguments of the original Fiche
should work as expected. `-u` is not implemented because, well, just use the
right user in the first place. 🤷‍♀️

### Recup Server

```bash
$ source venv/bin/activate
$ pyfiche-recup # try --help for options
```

### Lines Server

```bash
$ source venv/bin/activate
$ pyfiche-lines # try --help for options
```

## License

PyFiche is licensed under the MIT license. See the [LICENSE](LICENSE) file for
more information.
