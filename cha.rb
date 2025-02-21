# Formula: cha.rb
class Cha < Formula
  desc "A simple CLI tool for chatting with OpenAI's GPT, scraping, etc."
  homepage "https://github.com/MehmetMHY/cha"
  url "https://github.com/MehmetMHY/cha/releases/download/v0.13.1/cha-0.13.1.tar.gz"
  sha256 "6b2bc5142ccbd4ff47908c9cbe5738256c5af5efe54904a2e655dbd015bf9b79"
  license "MIT"

  # Your code says python requires >= 3.9.2
  depends_on "python@3.9"  # or "python" if you prefer

  def install
    # Create a private site-packages path in libexec
    ENV.prepend_create_path "PYTHONPATH", libexec/"lib/python3.9/site-packages"

    # This built-in helper sets up "python3 setup.py install ... --prefix=#{libexec}" 
    # and passes in the correct PYTHONPATH, so pip uses libexec as the install target.
    system "python3", *Language::Python.setup_install_args(libexec)

    # Symlink the 'cha' entrypoint script into Homebrew's bin/
    bin.install_symlink (libexec/"bin/cha")
  end

  # Basic test
  test do
    # Check that 'cha --help' runs
    system "#{bin}/cha", "--help"
  end
end

