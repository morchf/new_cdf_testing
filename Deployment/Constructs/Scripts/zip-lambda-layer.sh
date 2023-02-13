#!/bin/bash
# Zip a lambda layer

show_help() {
  echo "Usage: zip-lambda-layer [options...]"
  echo "  -r [requirements_file] Requirements file"
  echo "  -o [output_dir] Layer directory"
  echo "  -n [layer_name] Layer name"
}

while getopts "h?r:o:n:" opt; do
  case "$opt" in
    r)
      requirements_file=$OPTARG
      ;;
    o)
      output_dir=$OPTARG
      ;;
    n)
      layer_name=$OPTARG
      ;;
    h|\?)
      show_help
      exit 0
      ;;
    :) echo "Missing option argument for -$OPTARG" >&2; exit 1;;
  esac
done


pip install \
    -t $output_dir/$layer_name/python/lib/python3.8/site-packages \
    -r $requirements_file \
    --upgrade

(
    cd $output_dir/$layer_name;
    zip \
        -qr "${layer_name}.zip" \
        python;
    mv "${layer_name}.zip" "../${layer_name}.zip";
    cd ..;
    rm -rf $layer_name
)

echo "${output_dir}/${layer_name}.zip"
