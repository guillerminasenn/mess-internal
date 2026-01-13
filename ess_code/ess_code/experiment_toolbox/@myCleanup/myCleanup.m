% Prior to Matlab 6.5 it was possible to catch ctrl-c interrupts using
% try..catch blocks. Mathworks deliberately broke this and, according to their
% online help, didn't provide a workaround. Last time I looked Octave did trap
% ctrl-c. If not, look into "unwind_protect", as I don't think it will
% understand this class.
%
% Finally, Matlab 7.5 provides a documented solution called "onCleanup".
% I learned about it from here: http://blogs.mathworks.com/loren/2008/03/10/keeping-things-tidy/
% This file is a version of that. I worked out how onCleanup works from online
% sources, but haven't seen the actual implementation. I'll probably get access
% to Matlab 7.5 soon, but made this version because I didn't want to introduce a
% dependency in my code.

classdef myCleanup < handle
    properties
        fn = 0;
    end
    methods
        function obj = myCleanup(fn)
            obj.fn = fn;
        end
        function delete(obj)
            obj.fn();
        end
    end
end

