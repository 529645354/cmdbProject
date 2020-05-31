#!/bin/bash/expect
yum install -y tigervnc-server expect
expect "Password:"
exp_send "redhat\r"
expect "Verify:"
exp_send "redhat\r"
expect "*password (y/n)?"
exp_end "n"

