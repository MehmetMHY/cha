class Cha < Formula
  desc "A simple CLI tool for chatting with OpenAI's GPT, scraping, etc."
  homepage "https://github.com/MehmetMHY/cha"
  url "https://github.com/MehmetMHY/cha/releases/download/v0.13.1/cha-0.13.1.tar.gz"
  sha256 "6b2bc5142ccbd4ff47908c9cbe5738256c5af5efe54904a2e655dbd015bf9b79"
  license "MIT"

  depends_on "python@3.9"

  def install
    ENV.prepend_create_path "PYTHONPATH", libexec/"lib/python3.9/site-packages"
    system "python3", *Language::Python.setup_install_args(libexec)
    bin.install_symlink (libexec/"bin/cha")
  end

  test do
    system bin/"cha", "--help"
  end
end

