#!/bin/sh

rsync -avh nomad-summary/ .
rm -rfv nomad-summary
