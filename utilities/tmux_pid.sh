#!/bin/bash

#requires lsof, perl, pstree

file_tree() 
{
pid="$1"

indentation=$(printf "%${indent}s")

[[ "$$" -eq "$pid" ]] && printf "$yellow" 
echo "$indentation"$(ps -o pid= -o cmd= -p $pid | perl -pe 's/^\s+// ; s/\s+/,/')
printf "$reset" 

indent=$((indent + 3))

export indentation=$(printf "%${indent}s")
lsof -p $1 | perl -ane 'print "$ENV{indentation}$F[8]\n" if $F[8] ne "/bin/bash" && $F[4] eq "REG" && $F[3] ne "mem" '

for child in $(ps -o pid --no-headers --ppid $pid) ; do file_tree $child ; done

indent=$((indent - 3))
}

parse_it () 
{
reg_ex=$1
string=$2
shift 2

[[ $string =~ $reg_ex ]] || return 

i=1
for name; do
	declare -g "$name=${BASH_REMATCH[i++]}"
done
}

tmux_pstree() 
{
for s in `tmux list-sessions -F '#{session_id}:#{session_name}'` ; do
	parse_it '(.*):(.*)' "$s" session_id session_name

	echo -e "\n$light_blue===== session $s =====$reset"

	for p in $(tmux list-panes -s -F '#{window_index}:#{window_name}:#{pane_index}:#{pane_pid}' -t "$session_id") ; do
		parse_it '(.*):(.*):(.*):(.*)' "$p" window_index window_name pane_index pane_pid

		#printf "${light_blue}w:$window_index[$window_name], p:$pane_index, pid:"
		#file_tree  $pane_pid

		pstree -h -p -a -A $pane_pid

		echo
	done
done
}

tmux_pstree $@

