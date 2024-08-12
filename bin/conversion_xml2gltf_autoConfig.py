
import argparse
import ROOT
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description='Convert detector')
    parser.add_argument('-cm', '--compact_files', help='Compact file location(s)',
                        required=True, type=str, nargs='+')
    parser.add_argument('-cn_in', '--config_file_in', help='Json file of detector structure to be given',
                        default='', type=str)
    parser.add_argument('-cn_out', '--config_file_out', help='Automatic json file of detector structure file path out',
                        default='', type=str)
    parser.add_argument('-r_in', '--in_root', help='Input root file path (if a root file has already been obtained)',
                        default='', type=str)
    parser.add_argument('-r_out', '--out_root', help='Converted root file path',
                        default='', type=str)
    parser.add_argument('-g', '--out_gltf', help='Converted gltf file path',
                        default='', type=str)
    parser.add_argument('-d', '--depth', help='Level of layers in detector to consider in the conversion',
                        default=10, type=int)
    parser.add_argument('-hide', '--hidden_children', help='Parts of the detector to be hidden',
                        default=['thereisnodetectorparthere'], type=str, nargs='+')
    args = parser.parse_args()

    ## Loop for multiple compact files (currently not working)
    for cfile in args.compact_files: 
        ## For if both a root and config file are given               
        if args.in_root and args.config_file_in:
            config_file, root_path = args.config_file_in, args.in_root

        ## For if only a root file is given
        elif args.in_root and not args.config_file_in:
            config_file = automatic_config(args.config_file_out, cfile, args.depth, args.hidden_children)
            root_path = args.in_root

        ## For if only a config file is given
        elif not args.in_root and args.config_file_in:
            root_path = root_convert(cfile, args.out_root, args.depth)
            config_file = args.config_file_in

        ## For if neither file is given
        else:
            root_path = root_convert(cfile, args.out_root, args.depth)
            config_file = automatic_config(args.config_file_out, cfile, args.depth, args.hidden_children)
            
        gltf_convert(config_file, args.out_gltf, root_path)
                    
def root_convert(cfile, out_path, visibility):
    ## Converts an xml file to root file
    print('INFO: Converting following compact file(s):')
    print('      ' + cfile)

    ROOT.gSystem.Load('libDDCore')
    description = ROOT.dd4hep.Detector.getInstance()
    description.fromXML(cfile)

    ## Sets the number of layers visible in the root file
    ROOT.gGeoManager.SetVisLevel(visibility)
    ROOT.gGeoManager.SetVisOption(0)
    ## Sets an automatic root path if one isn't given
    root_path = determine_outpath(out_path, cfile, 'root')
    ROOT.gGeoManager.Export(root_path)

    return root_path

def automatic_config(config_out, cfile, depth, hide):
    ## Creates an automatic configuaration file if one isn't given using the 'configfile_generator.py'
    ## Determines automatic outpath of config file
    config_file = determine_outpath(config_out, cfile, "json")
    subprocess.run(["python", "configfile_generator.py", "--compact", f'{cfile}', '--max_depth', f'{depth}', '--config_path', f'{config_file}', '--hide_list', ', '.join(hide)])

    ## Asks the user if they would like to exit the run to edit the automatic config file
    config_edit = input(f'Would you like to exit and edit the automatic cofiguration file {config_file}? [y/n]')
    program_questions(config_file, config_edit, "c")
    
    return config_file


def gltf_convert(config, gltf, root):
    ## Converts the root file into a gltf file
    ## Determines the outpath of the gltf file if one isn't given
    gltf_path = determine_outpath(gltf, root, "gltf")
    subprocess.run(["node", ".", "-c", f'{config}', "-o", f'{gltf_path}', f'{root}'])

    ## Asks the user if they would like to remove the root file
    rmv_file = input(f'Would you like to remove the {root} file? [y/n]')
    program_questions(root, rmv_file, 'r')

def determine_outpath(out_path, file, ending):
    ## Generates the automatic out_paths for the files if one isn't provided
    if out_path == '':
        counter = 0
        slash_list = []
        for i in file:
            counter += 1
            if i == '/':
                slash_list.append(counter)
            if i == '.':
                dot = counter

        if not slash_list:
            path = f'../{ending}_files/{file[:dot-1]}.{ending}'
        else:
            last_slash = max(slash_list)
            if ending == 'json':
                path = f'../configs/{file[last_slash:dot-1]}.{ending}'
            else:
                path = f'../{ending}_files/{file[last_slash:dot-1]}.{ending}'          
    else:
        path = out_path
    return path

def program_questions(file, response, r_c):
    ## Asks questions to user as described above
    while True:
        if response == 'y':
            if r_c == 'r':
                print(f'Removing {file} file')
                os.remove(file)
                break
            elif r_c == 'c':
                print('Exiting converter')
                exit()
        elif response == 'n':
            if r_c == 'r':
                print(f'{file} file kept')
            elif r_c == 'c':
                print('Producing gltf file:')
            break
        else:
            print("Incorrect response given (choose y/n)")
            response = input()

if __name__ == '__main__':
    main()