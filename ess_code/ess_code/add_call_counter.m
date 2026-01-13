function fn2 = add_call_counter(fn, varargin)
%ADD_CALL_COUNTER wrap a function so that calls to it are counted
%
%     fn2 = add_call_counter(fn, varargin);
%
% Now fn2 will behave exactly like fn, unless its arguments are exactly the same
% as varargin, in which case a call count will be returned and the counter will
% be reset. Set varargin to the simplest set of arguments that can never be
% passed to fn().
%
% Example:
%     fn2 = add_call_counter(fn, {});
%     ans1 = fn2(arg1, arg2);
%     ans2 = fn2(arg1, arg2);
%     num_calls = fn2({}); % num_calls == 2, counter is reset
%     ans3 = fn2(arg1, arg2);
%     num_calls = num_calls + fn2({}); % num_calls == 3, counter reset again.
%
% Inputs:
%               fn @fn handle to function that needs wrapping
%         varargin  ?  if fn2 is called with exactly this set of arguments
%                      (can be empty) then instead of calling fn, it returns the
%                      number of calls since the last reset & resets the counter
%
% Outputs:
%              fn2 @fn function that behaves just like fn unless its input
%                      arguments are varargin. Then a call count is reported and
%                      the counter reset.

% Iain Murray, August 2009

% NOTE: this wasn't written with a huge number of counters in mind. The
% mechanism that allows multiple counters doesn't scale well as Matlab doesn't
% seem to use a hash lookup for its structure fields. Also, if fn2's counter
% isn't reset before fn2 goes out of scope, then memory will be leaked. Fancy
% Matlab handle class stuff could be used to avoid this, but the current version
% fits my needs and I wanted to write something that would work in Octave too.

% Set up unique identifier for this counter
persistent next_id
if isempty(next_id)
    next_id = 0;
end
id = sprintf('a%d', next_id);
next_id = next_id + 1;

% Create wrapped function
flag_args = varargin;
fn2 = @(varargin) call_counter_helper(id, fn, flag_args, varargin);


function varargout = call_counter_helper(id, fn, flag_args, fn_args)

persistent counter
if isempty(counter)
    counter = struct();
end

if isequal(fn_args, flag_args)
    % Special set of arguments, return call count and flush counter
    if isfield(counter, id)
        varargout{1} = counter.(id);
        counter = rmfield(counter, id);
    else
        varargout{1} = 0;
    end
else
    % Count the function call
    if isfield(counter, id)
        counter.(id) = counter.(id) + 1;
    else
        counter.(id) = 1;
    end
    % And behave like the original function
    varargout = cell(1, max(1, nargout));
    [varargout{:}] = fn(fn_args{:});
end

