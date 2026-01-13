function save_struct(filename, strct)
%SAVE_STRUCT hack for old Octave not supporting save(filename, '-struct', strct)
%
%     save_struct(filename, strct)
%
% Saves a Matlab V7 .mat file containing the elements of strct as top-level
% variables.
%
% Inputs:
%     filename string
%        strct structure

% Iain Murray, January 2009

% The version of Octave I have installed doesn't support '-struct' in save
% commands. I found a patch online, but it seems likely that it will take a
% while for this to filter through to people's desktops. This is a quick work-around.

% SAVE is quite limited. The names saved into the .mat file are the same as in
% the local scope. a) I have to put the strct variables into the local scope. b)
% I have to hope they don't clash with other variables I need. This is why I use
% such ugly variable names here. I can think of convoluted ways to allow fields
% in strct to begin with 'yHjqioPz_', but I don't think it will ever be a
% problem in my code, and the real solution is to upgrade Octave.

if ~sum(filename == '.')
    filename = [filename, '.mat'];
end

yHjqioPz_filename = filename;
yHjqioPz_args = fieldnames(strct);
yHjqioPz_strct = strct;

% Otherwise bad things happen:
assert(~ismember('yHjqioPz_args', yHjqioPz_args));
assert(~ismember('yHjqioPz_filename', yHjqioPz_args));
assert(~ismember('yHjqioPz_field', yHjqioPz_args));

for yHjqioPz_field = yHjqioPz_args(:)'
    eval([yHjqioPz_field{1}, ' = yHjqioPz_strct.', yHjqioPz_field{1}, ';']);
end

save('-v7', yHjqioPz_filename, yHjqioPz_args{:});
