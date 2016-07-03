#test2test

Convert between C++ testing frameworks.  I wrote this for personal use, so it just does what I
needed it to do.  But I believe it's easily extensible - contributions welcome.

##Background
I wanted to try switching IDEs from [Eclipse CDT](http://www.eclipse.org/cdt/) to
[CLion](https://www.jetbrains.com/clion/).  I was using 
[Boost.Test](http://www.boost.org/doc/libs/1_61_0/libs/test/doc/html/index.html) but CLion only
supports the [Google C++ Testing Framework](https://github.com/google/googletest), so I wrote a 
little Python script to convert my tests.

Then I discovered the awesome [Catch](https://github.com/philsquared/Catch), which allows for
BDD style tests (like [Jasmine](http://jasmine.github.io/) for Javascript).  So I adapted the 
script to support Catch as well.

##Caveats
* Currently only supports
  - [Boost.Test](http://www.boost.org/doc/libs/1_61_0/libs/test/doc/html/index.html) => 
  [Google C++ Testing Framework](https://github.com/google/googletest)
  - [Boost.Test](http://www.boost.org/doc/libs/1_61_0/libs/test/doc/html/index.html) => 
  [Catch](https://github.com/philsquared/Catch)
* There is some support for clever matches, but it's probable that comments/strings containing e.g.
  brackets, may confuse the parsing.
* Fixtures are annoying to convert.  If you use fixtures you will get compilation errors - there is
  some manual tidying that has to be done after using the script.
  - Google: fixtures must have unique names, and must inherit from `testing::Test`.  The script
    will rename the fixtures in the tests, but the fixture class itself will have to be manually
    updated.
  - Catch: fixtures must have unique names and must be at the root of the testing hierarchy.  The
    script will move fixture tests out of the `SCENARIO` block to the bottom of the file.  Thus
    you will have to move the fixture classes next to them.
  - The script will log to the console when fixtures have to be updated.
* You will have to configure the `main` entry point as per the testing framework manually.
  

##Command line
```
$ ./test2test --help
usage: test2test [-h] -i FROM -o TO [-f GLOB] [-p PREFIX] [-s SUFFIX] [-d]

Convert between c++ testing frameworks.

optional arguments:
  -h, --help            show this help message and exit
  -i FROM, --from FROM  Test type from
  -o TO, --to TO        Test type to
  -f GLOB, --glob GLOB  File path glob for files to convert (default *.cpp)
  -p PREFIX, --prefix PREFIX
                        Prefix for generated files (default [TO])
  -s SUFFIX, --suffix SUFFIX
                        Suffix for generated files
  -d, --dry-run         Log to console rather than writing files
```

```
$ ./test2test -i boost -o catch -f "../Felt/src/tests/test_*.cpp"
```
