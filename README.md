# PyCkSum

## Summary

PyQt-based GUI tool for checksum calculation of a single file

## Usage

In POSIX or Linux environment, make sure the file `pycksum.py` is executable
and is symlinked to a `$PATH`-recognizable location with the name `pycksum`.
After that, the command may be launched in the following way:

```
pycksum <commands> <file>
```

where

- `<commands>` is a comma-separated list of hash computing tools
  available in the system;

- `<file>` is a file to be processed

For example,

```
pycksum crc32,md5sum,sha1sum ./foo.bar
```

In FreeDesktop-compliant environments, the tool can be integrated into the
system GUI by means of `pycksum.desktop` file (the reference example published
here is intended to be used within KDE environments)

## License

MIT License
