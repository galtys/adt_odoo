{ pkgs ? import <nixpkgs> {} }:

let

#with import <nixpkgs> {};
#python.withPackages (ps: with ps; [ numpy toolz ])
#ebaysdk num2words pyldap vatnumber xlswriter
#libsass
  #libsass-python
   my_vatnumber = pkgs.python37.pkgs.buildPythonPackage rec {
      pname = "vatnumber";
      version = "1.1";
      src = pkgs.fetchurl {
         url = "https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/vatnumber/vatnumber-1.1.tar.gz";
         #sha256 = "0c9ims85skikr2ciw06nzgk639r1sg1x1adc2ja24yiy93nnkz70";
         sha256 = "065fgz042ca2iy7kkjjhglqsavn82sxfdnz09jkhjxhk1r11fw7z";
      };
      #src = python27.pkgs.fetchPypi {
      #  inherit pname version;
      #  sha256 = "0kbr95a85812drvhhnwrqq3pb85xq5j7i5w9bscl9m8b7im315hv";
      #};
      
      doCheck = false;
      propagatedBuildInputs = [  ] ;
      meta = {
        homepage = "";
        description = "vatnumber";
      };
    };

    my_libsaass = pkgs.python37.pkgs.buildPythonPackage rec {
      pname = "libsass";
      version = "0.12.3";
   
      src = pkgs.python37.pkgs.fetchPypi {
        inherit pname version;
        #sha256 = "15dyw3xm1sf22c52vbznjdj2hxn09i3h8awqw1adk8afghd6snwb";  0.19
        sha256 = "1c3kcr0hhqvyxkxp8qab97wpmlkpb95gyr9dv4pbffv9kjpn4rr3";
        
      };
      propagatedBuildInputs = [ pkgs.python37.pkgs.six pkgs.python37.pkgs.suds-jurko] ;
#      src=pkgs.fetchFromGitHub {
#        owner = "sass";
#        repo = "libsass-python" ;
#        rev = "58e19c041f2ff15a2eafced81e3b5f752f73abf9";
#        sha256 = "0ahibbcmm9ky4mmrmi4cq8hi803id4g4vkf05sb6a60lagibv65x";
#      };
      doCheck = false;

      meta = {
        homepage = "https://github.com/sass/libsass-python/";
        description = "libsass-python: Sass/SCSS for Python";
      };
    };

    my_hashsync = pkgs.python37.pkgs.buildPythonPackage rec {
      pname = "hashsync";
      version = "0.1";


      #      src = super.fetchFromGithub {
      #    owner = "galtys";
      #    repo = "hashsync";
      #    rev = "eecbfedac48f827e96ad5e151de8f41f6cd3af66";
      #    sha256 = "0rs9bxxrw4wscf4a8yl776a8g880m5gcm75q06yx2cn3lw2b7v22";
      #  };
      src = "";

      meta = {
        homepage = "https://galtys.com";
        description = "";
      };
    };



    my_werkzeug  = pkgs.python37.pkgs.buildPythonPackage rec {
       pname = "Werkzeug";
       version = "0.16.1";

       src = pkgs.python37.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "b353856d37dec59d6511359f97f6a4b2468442e454bd1c98298ddce53cac1f04";
       };

       propagatedBuildInputs = [ pkgs.python37.pkgs.itsdangerous ];
       checkInputs = [ pkgs.python37.pkgs.pytest pkgs.python37.pkgs.requests pkgs.python37.pkgs.hypothesis pkgs.python37.pkgs.pytest-timeout ];

       #checkPhase = ''
       #  pytest ${stdenv.lib.optionalString stdenv.isDarwin "-k 'not test_get_machine_id'"}
       # '';

       meta =  {
          homepage = "https://palletsprojects.com/p/werkzeug/";
          description = "A WSGI utility library for Python";
	      
          };
	};


    my_inotify = pkgs.python37.pkgs.buildPythonPackage rec {
      pname = "inotify";
      version = "0.2.10";
   
      src = pkgs.python37.pkgs.fetchPypi {
        inherit pname version;
        #sha256 = "15dyw3xm1sf22c52vbznjdj2hxn09i3h8awqw1adk8afghd6snwb";  0.19
        sha256 = "01raq3v0vpycjqzgr0462zn37vb3p1gp1syl2qpbd0l46cx64jlp";
        
      };
      propagatedBuildInputs = [pkgs.python37.pkgs.nose ] ;
      doCheck = false;

      meta = {
        homepage = "https://pypi.org/project/inotify";
        description = "inotify ";
      };
    };

    
#pyldap, vatnumber, pypiwin32 my_libsaass
  mypython = pkgs.python37.buildEnv.override {
  extraLibs = with pkgs.python37Packages; [Babel chardet decorator docutils feedparser gevent greenlet html2text jinja2   lxml Mako markupsafe mock num2words ofxparse passlib pillow psutil psycopg2 pydot  pyparsing pypdf2 pyserial python-dateutil pytz pyusb qrcode reportlab requests suds-jurko vobject my_werkzeug XlsxWriter xlwt xlrd polib setuptools pip my_libsaass python-stdnum my_vatnumber watchdog unicodecsv my_inotify pysftp networkx];  
  ignoreCollisions = true;
  };

in

pkgs.stdenv.mkDerivation rec {
  name = "env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };
  buildInputs = [
    mypython
    pkgs.python37Packages.ipython
    pkgs.lxc
    pkgs.lessc
 #   pkgs.nodejs
#    pkgs.sassc
    pkgs.wkhtmltopdf
    #pkgs.python
    #pkgs.python27Packages.virtualenv
    #pkgs.python27Packages.pip
    #pkgs.go_1_4
    #pkgs.lua5_3
  ];
}
