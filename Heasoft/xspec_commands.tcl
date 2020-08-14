#Procedures for dealing with combinations of models and simplifying life.
set XSPEC_COMMANDS_FILE [info script]

namespace eval xspec_commands {
set c 299792
array set help_array {}
    
proc %proc { name arguments body {help "No help provided."} } { 
    global ::xspec_commands::help_array
    proc $name $arguments $body
    set help_array($name) "$help"
} 

%proc printComps { ptype  {fname ""}} {
    set N [tcloutr modcomp]
    set inds [get_ind norm]
    foreach i $inds {
        lappend vals [lindex [tcloutr param $i] 0]
        newp $i 0
    }
    set columns {}
    set map {}
    set to  {}
    for {set i 0} {$i < [llength $inds]} {incr i} {
        newp [lindex $inds $i] [lindex $vals $i]
        set last [setplot command wd component.qdp]
        plot $ptype
        delete $last
        lappend map x$i [load_table component.qdp " " 3 end]
        file delete component.qdp
        set to [concat $to \$x$i]
        newp [lindex $inds $i] 0
    }
    for {set i 0} {$i < [llength $inds]} {incr i} {
        newp [lindex $inds $i] [lindex $vals $i]
    }
    set last [setplot command wd component.qdp]
    plot $ptype
    delete $last
    lappend map d [load_table component.qdp " " 3]
    set to [concat {{*}$d} $to]
    file delete component.qdp

    set res [lmap {*}$map "list $to"]
    if { $fname == "" } {
        return $res
    }
    with $fname.qdp w fd {
        puts $fd "READ SERR 1 2"
        puts $fd "@$fname.pco"
        puts $fd "!"
        puts $fd [join $res \n]
    }
    return 0
} "Create a data file containing the model components with the data. Yes, XSPEC does not provide this as far as I know..."

%proc load_table { fname {delim " "} {skip_rows 0} {name_col -1} args }  {
    with $fname r fd {
        if {[llength $args] == 1} {
            set args [concat $args $args]
        } elseif {! [llength $args]} {
            set args {0 end} 
        }
        set result []
        while { [gets $fd line] > -1 } {
            if { $skip_rows } {
                incr skip_rows -1
                continue 
            }
            set cur [lrange [split [regsub -all "$delim+" $line  "$delim"] $delim] {*}$args]
            if { [lindex $cur end] == "" } {
                set cur [lreplace $cur end end]
            }
            if { $name_col > -1 } {
                set name [lindex $cur $name_col]
                set cur [lreplace $cur $name_col $name_col]
                lappend result $name $cur
            } else {
                lappend result $cur
            }
        }
    }
    return $result
} "Load a table as a list of lists or array depending on name_col."

%proc help_commands { command } {
    global ::xspec_commands::help_array
    if { ![regexp " $command |^$command | $command\$" [list_commands 0]]} {
        puts "-E- No such command! To list loaded commands hit list_commands."
        return
    }
    set msg [split $help_array($command) "\n"]
    foreach line $msg { 
        puts "-I- $line"
    }
} "Help for custom XSPEC commands."

%proc show_comp { comps {index 0} } {
    global SHOWVARS
    set show ""
    foreach comp $comps {
        set count 0
        set pars [get_comp $comp]
        foreach component $pars {
            incr count
            if { $index && $index != $count } continue
            lassign [tcloutr compinfo $component] _ first length
            set show "$show $first-[expr $first+$length-1]"
        }
    }
    set SHOWVARS $show
    showw
} "Show all parameters of component index or name. If two arguments are used will assume the the component is the arg2 component named arg1."

%proc get_comp { name } {
    if { [string is integer $name] } { return [list $name] }
    set res [list]
    for {set i 1} {$i <= [tcloutr modcomp]} {incr i} {
        if { [string match ${name}* [lindex [tcloutr compinfo $i] 0]] } {
            lappend res $i
        }
    }
    return $res
} "Get all component indices with name. If an integer is given return a list containing that integer."

%proc list_commands { {newline 1} } {
    global XSPEC_COMMANDS_FILE

    set fd [open $XSPEC_COMMANDS_FILE]
    set commands {}
    foreach c [regexp -inline -all -line {^%proc\s+[^\s%]*} [read $fd]] {
        set command [lindex $c 1]
        if { [llength $command] } { lappend commands [regsub {xspec_commands::} $command ""] }
    }
    close $fd
    if { $newline } {
        foreach command $commands {
            puts "-I- $command"
        }
        return
    }
    return $commands
} "List loaded custom XSPEC commands. Giving 0 as an argument will return a list."

%proc get_indices { paramOrComp {pars {}} } {
    set res {}
    set indices {}
    set params $paramOrComp
    set comps {-1}
    if { $pars != {} } {
        set comps [get_comp $paramOrComp]
        set params $pars
    }
        
    foreach param $params {
        foreach comp $comps {
            set first 1
            set length [tcloutr modpar]
            if {$comps > 0 } {
                lassign [tcloutr compinfo $comp] _ first length      
            }
            for {set i $first} {$i<[expr {$first+$length}]} {incr i} {
                if {[string compare -nocase [lindex [tcloutr pinfo $i] 0] $param]==0} {
                    lappend res $i
                }
            }
        }
    }
    return $res
} "Retrieve indices of given elements. Should work with any parameter. Case insensitive. If an element name appears more than once, all indices will be retrieved. If a second argument is given the first will assumed to be the component name or number, and the second the parameter name." 

%proc get_elems { indices } {
    set res {}
    foreach i $indices {
        lappend res [lindex [tcloutr pinfo $i] 0]
    }
   return $res 
} "Retrieve parameter name of given indices."

%proc tie_vars {indices comp_step {ratio none} {action *} {comps -1} {initial ---} {no_tie 0} {hard_limit Inf} } {
    foreach j $indices {
        if {$initial != "---"} {
            newpar $j $initial 
        }
        set counter $comps
        for {set i 1} {[expr $i*$comp_step + $j] <= [tcloutr modpar]} {incr i} { 
            set next_index [expr $i*$comp_step + $j]
            if { $ratio == "none" } {
                newpar $next_index=$j
            } else {
                set bot [lindex [tcloutr param $next_index] end-3]
                set top [lindex [tcloutr param $next_index] end]
                set res [expr [get_abund $j] ${action} $ratio*double($i)]
                if { $res > $top || $res < $bot } {
                    tclerror "Out Of Bound in tie_vars- went beyond model."
                }
                if { ! $no_tie } {
                    newpar $next_index=${j}${action}([expr $ratio*double($i)])
                } else {
                    newpar $next_index $res
                }
            }
            incr counter -1
            if { ! $counter } break
        }
    }
} "Tie all subsequent parameters in jumps of comp_step to indices.
All subsequent parameters for a given index 7 will be 'newpar subsequent_index=7 action ratio*component_number.'
'action' is some arithmetic to perform, commonly addition or multiplication.
If there are 3 components the final 2 will be tied to ratio and ratio*2 added/multiplied/etc to parameter 7.
This may be used to tie vars with ratio=0.0 and action=+.

Setting initial will set the parameter in the first model (all indices given will be the same) and 'no_tie' will
perform the action but will not tie the parameters together. 'comps' argument is the amount of consecutive runs - do
not forget that the first model should not be counted here!."

%proc set_vars { pars {perform "puts"} {perform_end ""} {step ""} {comps 999999} } {
    foreach initial $pars {
        set counter $comps
        while { $initial <= [tcloutr modpar] } {
            eval $perform $initial $perform_end
            if { $step != "" } {
                incr counter -1
                if { ! $counter } break
                set initial [expr $initial + $step]
            } else {
                break    
            }
        }
    }
} "Perform the same operation on multiple parameters. For each parameter the command will be:
perform parameter perform_end

If step is given then the same will be done for all parameters in a multiples of 'step' away from the 
given parameters, for all possible parameters. In this case 'comps' may be given to limit amount of iterations."

%proc locate_elems { initial step compnum } {
    set el {}
    foreach e $initial {
        lappend el [expr $e+$step*($compnum-1)]
    }
    return $el
} "Get the indices of the parameters given in initial, compnum*step ahead. Useful to obtain parameter indices of
models using the same basic model several times."

#Returns only value of given parameter.
%proc get_abund { param } {
    if { ! [string is integer $param] } {
        set param [get_indices $param]
    }
    set res {}
    foreach i $param {
        lappend res [lindex [split [tcloutr param $i]] 0]
    }
    return $res
} "Return value of given parameter. Can be name or index. If name, and appears more than once, all occurences will be retrieved."

%proc get_abunds { params } {
    set res [list]
    foreach i $params {
        set res [concat $res [get_abund $i]]
    }
    return $res
} "Return value of given parameters. If parameters given as names, parameters with the same name will appear as many times as they appear."

%proc freeze_table { to indices } {
    foreach elem $indices {
        if { $elem == $to } { continue }
        newpar $elem = $to * [expr double([get_abund $elem])]/[get_abund $to] 
    }
} "Retain (tie) all ratios between each index in indices and 'to'. All parameters in indices will be tied thus to 'to'." 
%proc init_model { model it {math +} {extra ""} } {
    ignore bad 
    set mod $model
    for {set i 1} {$i < $it} {incr i} { 
        set mod "$mod$math$model"    
    }
    if { $extra != "" } {
        model ($extra)$math$mod & /*
    } else { model $mod & /*}
} "Creates a concated model. When adding multiple same models (or multiplying) this is useful. Extra will be prepended
to model."

%proc set_color { {unicolor 0} } {
    if { $unicolor } {
        for { set i 1 } { $i <= [tcloutr datasets] } {incr i} {
            setplot command color 1 on [expr {2*$i-1}]
            setplot command color 2 on [expr {2*$i}]
        }
    } elseif { [tcloutr model] != "" } { 
        for { set i 1 } { $i <= [tcloutr datasets] } {incr i} {
            setplot command color [expr [tcloutr datasets] + 1] on [expr {$i*2}]
        }
    }
}

%proc delete { command {amount 1} } {
    global _x_RESIZE
    global _y_RESIZE
    unset -nocomplain _x_RESIZE
    unset -nocomplain _y_RESIZE
    if { $command == "last" } {
        set command [setplot command fake]
        incr command -1
        set amount 2
    }
    for {set i 0} {$i < $amount} {incr i} {
        setplot delete $command
    }
} "setplot delete starting from command amount commmands. 'last' works."

%proc panel_plot { {noaxes 0} } {
   setplot command LABEL POS Y 1.8
   setplot command WIN 1
   if { $noaxes } {
       setplot command VI 0.05 0.35 0.95 0.95
       setplot command LAB X "" 
       setplot command LAB Y "" 
       setplot command LAB NX OFF 
       setplot command LAB NY OFF 
   } else {
       setplot command VI 0.1 0.4 0.95 0.95
   }
   setplot command WIN 2
   if { $noaxes } {
       setplot command VI 0.05 0.05 0.95 0.35
       setplot command LAB X "" 
       setplot command LAB Y "" 
       setplot command LAB NX OFF 
       setplot command LAB NY OFF 
   } else {
       setplot command VI 0.1 0.15 0.95 0.4
   }
   setplot command WIN all
   setplot command LAB ROTATE
   setplot command LAB 2 COL 2
} "Add 6 commands to setplot viewport in a two panel plot."

%proc splist {} {
    setplot list
} "Alias for setplot list."

%proc pretty_plot { {contour 0} {unicolor 0} } {
    delete all 
    setpl wave
    setpl wave perhz off
    setpl area
    setpl comm LAB  titl "" 
    setpl comm time off 
    setpl comm lw 8 
    setpl comm csize 1.8
    for {set i 1} {$i < 13} {incr i} {
        setpl comm lw 8 $i
    }
    set_color $unicolor
    if { $contour == 1 } {
        setpl comm contour lw 8 8 8 
        setpl comm LABEL 10 \\\" \\\"
    }
    setplot command VI 0.1 0.12
    setplot xlog off
    return [setplot command LAB  Y  Flux (ph s\\u-1\\d \\A\\u-1\\d cm\\u-2\\d)]
} "My plot preferences. Use pretty_plot 1 when plotting contours. If plotting data after, you must use pretty_plot
with no parameters or no plot will be shown."

%proc pretty_eplot { {contour 0} {unicolor 0} } {
    delete [pretty_plot $contour $unicolor]
    setplot energy
    setplot command LAB  Y  Flux (ph s\\u-1\\d keV\\u-1\\d cm\\u-2\\d)
} "Same as pretty plot, for energy."

%proc count_expr { exp str } {
    return [regsub -all $exp $str - fake]
} "Count how many times exp appears in str."

%proc count_words { str } { 
    return [count_expr {[^\s]+} $str]
} "Count how many words are in str."

%proc rgs_load { whats {index ""} {preglob ""} {postglob ""}} {
    foreach what $whats {
        if { $what == "data" } {
            set glb SRSP 
        }
        if { $what == "daba" } {
            set what data
            set glb SBSP 
        }
        if { $what == "resp" } {
            eval $what $index [regsub -all SRSPEC. [lsort [glob *SRSP*]] RSPMAT1]
            set glb RSPM 
            break
        }
        if { $what == "back" } {
            set glb BGSP 
        }
        eval $what $index [lsort [glob *$preglob*$glb*$postglob*]]
    }
} "Useful XMM-RGS pipeline file loader. Can load multiple data/response/background files if XMM naming convention used.
Won't work with other devices such as PN and MOS."

%proc pha_load { {pha_filter ""} {load_resp 0}} {
    if { $load_resp } {
        error "Not implemented"
    }
    set data {} 
    set back {} 
    foreach {first secon} [glob $pha_filter*.pha] {
        if { [string length $first] > [string length $secon] } {
            lappend data $secon     
            lappend back $first
        } else {
            lappend data $first
            lappend back $secon
        }
    }
    eval data $data
    eval back $back
} "Loads .pha files as data, where background is expected to be the longer name than the source. Will also load response as .rmf and arf as .arf. Filter may be used incase of multiple pha."

%proc make_ign { ranges } {
    set bo ""
    foreach r $ranges { set bo "ignore $r;$bo"}
    %proc ::ign {} [list eval $bo]
    ign
} "Ignore ranges (which is any legal ignore string) and create a procedure called 'ign' for quickly ignoring the same
ranges."

%proc rebin { { sigma 1 } { count 1 } { dataset "" }} {
    setplot rebin $sigma $count $dataset
} "For lazy people."

%proc range args {
    set length [llength $args]
    set start 0
    set step 1
    switch $length {
        1 {
            set end [lindex $args 0]
        }
        2 {
            foreach {start end} $args break
        } 
        3 {
            foreach {start end step} $args break
        }
        default {
            return []
        }
    }
    for {set res []; set x $start} {$x<=$end} {set x [expr $x+$step]} {
        lappend res $x
    }
    return $res
} "Generate a range of numbers. 
'range a ?b ?c'
Will return all numbers between a and b with jumps of c. If less then 3 parameters are given 'step' is assumed to
be 1, and if less then 2 start is assumed to be 0."

%proc print_params { {type free} {verbose 0} } {
    set chatter [tcloutr chatter]
    chatter 0
    set log /tmp/nochanceofthisfileexisting
    log $log
    show $type
    log none

    set fp [open $log r]
    set log [read $fp]
    close $fp

    set res {}
    foreach par [split $log "\n"] {
        set current [list newp [lindex $par 1]]
        if { [lindex $par end] == "frozen" } { 
            lappend current [lindex $par end-1] 
        } elseif { [lindex $par end-1] == "+/-" } { 
            lappend current [lindex $par end-2] 
        } else { 
            if { $verbose} { puts "Error dealing with line '$par.'"} 
            continue
        }
        lappend res $current
    }
    eval chatter $chatter
    return $res
} "Note this creates a log file in your directory. Generates a list of parameters for ease of use, for example initializing free variables or all parameters. 'type' is given to 'show' and the output is analyzed. Only 'all' and free are supported."

%proc free_list {} {
    set old_chatter [tcloutr chatter]
    chatter 10 10
    set x {}
    foreach a [print_params] {
        lappend x [lindex $a 1]
    }
    chatter {*}$old_chatter
    return $x
} "A list of free parameters."

%proc lshift {lst params {arith +} } {
    set r {}
    foreach x $lst {
        lappend r [expr $x $arith $params]
    }
    return $r
} "Perform 'arith params' for each element in lst. For instance adding 1 to all elements will be:
lshift \$my_list 1."

%proc setcom { args } {
    setplot command $args
} "For lazy setplot command."

%proc resize { xory min {max ""} } {
    global _y_RESIZE _x_RESIZE
    if { ! [in {x y} $xory] } {
        puts "-E- First argument must be 'x' or 'y'."
        return
    }
    if { [info exists _${xory}_RESIZE] } {
        delete [set _${xory}_RESIZE]
    }
    set _${xory}_RESIZE [eval setcom "resize $xory $min $max"]
} "Lazy setplot command resize."

%proc init_plot {} {
    pretty_plot
    cpd /xw
    ignore bad
    plot
} "Initialize pretty_plot"

%proc rgs_multi_init { dirs args } {
    set cwd [pwd]
    foreach d $dirs {
        cd $d
        eval rgs_init [expr {[tcloutr datasets]+1}] $args
        cd $cwd
    }
} "Call rgs_init without overwriting loaded spectra"

%proc rgs_init { {index ""} {preglb *} {postglb *} {no_resp 0} {include_back 0} {additional_cmd {}} } {
    rgs_load data $index $preglb $postglb
    if { ! $no_resp } { rgs_load resp $index $preglb $postglb }
    if { $include_back } { rgs_load back $index $preglb $postglb }
    foreach cmd $additional_cmd { eval $cmd }
    if { $index == "" } {
        init_plot
        ignore **:0.0-8.0,37.0-**
        plot
    }
} "Load data, and init plot, ignore bad and plot. Can stop response loading or foce background check. Additional commands can be run."

%proc showw { args } {
    global SHOWVARS
    if { $args != {} } {
        set SHOWVARS $args
    }
    show param $SHOWVARS
} "Easily view a subset of the parameters, with normal show syntax."

%proc loadlibs {} {
    global env
    return "lmod xstarmod; lmod tbnewmodel; lmod relxill"
} "command to load my favorite XSPEC addons"

%proc enumerate { somelist { start 1 } } {
    set num $start
    foreach element $somelist {
        lappend result [list $num $element]
        incr num
    }
    return $result
}

%proc clean0bins {} {
    set temp "temporaryQdp.qdp"
    set dumpQdp [setplot command wd $temp]
    plot
    delete $dumpQdp
    set fd [open $temp]
        set count 0
        while { [gets $fd line] > -1} {
            incr count
            set ignore "ignore $count:"
            while { [gets $fd line] > -1 && $line != "NO NO NO NO\n"} {
                set data [lindex $line 2] 
                if { $data == 0 } {
                    set xval [lindex $line 0]
                    set ignore "$ignore$xval,"
                }
            }
            eval $ignore
        }
    plot
    file delete $temp
}

%proc lindices { lst args } {
    foreach x $args {
        lappend ret [lindex $lst $x]
    }
    return $ret
} "Get several indices from list"
%proc lapply {lambda a} {
    foreach x $a {
        lappend ret [apply $lambda "$x"]
    }
    return $ret
} "Apply lambda to list a"
%proc lmerge {a b func {check {{x} {return $x}}}} {
    set len  [llength $a]
    set last [expr {[llength $b]-1}]
    set res {}
    for {set i 0} {$i<$len} {incr i} {
        set j $i
        if {$j > $last} {set j $last}
        set ai [apply $check [lindex $a $i]]
        set bj [apply $check [lindex $b $j]]
        lappend res [apply $func $ai $bj]
    }
    return $res
} "Merge two lists"
%proc lzip {args} {
    set lengths [lapply {{x} {llength $x}} $args]
    set lim 0
    foreach m $lengths {
        if { $lim < $m } {set lim $m}
    }
    for {set i 0} {$i < $lim} {incr i} {
        lappend result [concat {*}[lapply "{x} {lindex \$x $i}" $args]]
    }
    return $result
}
foreach op {+ - * /} {
    %proc ${op}= { a b {check {{x} {return $x}}}} "        
        upvar \$a t
        set res \[lmerge \$t \$b {{x y} {expr {\$x$op\$y}}} \$check]
        set t \[concat \$res \[lrange \$b \[llength \$t] end]]
    " "Operator assignment."
    namespace export ${op}=
}
%proc dot { a b } {
    set res 0
    for {set i 0} {$i < [llength $a]} {incr i} {
        += res [expr {[lindex $a $i]*[lindex $b $i]}]
    }
    return $res
} "Dot product"

%proc sum { a } {
    set res 0
    foreach x $a { += res $x }
    return $res
} "Sum list"
%proc in { lst x } {
    foreach a $lst {
        if { $a == $x } {
            return 1
        }
    }
    return 0
}

%proc nh { obj } {
    return [expr {[exec nhtool.bash -num $obj]/1e22}]
}

%proc outflowZ { z V } {
    set c $::xspec_commands::c
    return [expr {($c*$z-$V)/$c}]
} "Get Z of blueshifted outflow by V relative to z"

%proc loadTable {fname delim {arrname ""}} {
    if { "$arrname" != "" } {
        upvar $arrname arr
        unset -nocomplain arr
    }
    set fd [open $fname]
    while { [gets $fd line] > -1 } { 
        set row [lapply {x {string trim $x}} [split $line $delim]]
        if { "$arrname" != "" } {
            set arr([lindex $row 0]) [lrange $row 1 end]
        } else {
            lappend data $row 
        }
    }
    close $fd
    if { "$arrname" != "" } return
    return $data
}
%proc mkpshow {what} {
    if { [string match [string tolower $what] pl] } return
    proc ::$what {} "
        global SHOWVARS
        set SHOWVARS \[get_ind $what\]
        showw
    "
    if { [string match $what [string tolower $what]] } return
    proc ::[string tolower $what] {} "$what"
} "Make a function <what> that shows all parameter values of what"

%proc mkallpshow {} {
    if { [tcloutr model] == "" } return
    for {set i 1} {$i<=[tcloutr modpar]} {incr i} {
        mkpshow [lindex [tcloutr pinfo $i] 0]
    }
} "Make a pshow proc for each parameter"

%proc with {fname mode fdesc body} {
    upvar $fdesc fd
    if { $fname != "stdout" } {
        set fd [open $fname $mode]
            uplevel $body
        close $fd
    } else {
        set fd stdout
        puts [uplevel $body]
    }
} "Some syntactic sugar to open a file"

%proc showp { args } {
    show para [eval get_indices $args]
} "Show parameters with human syntax"

%proc freezep { args } {
    freeze [eval get_indices $args]
} "Freeze parameters with human syntax"

%proc thawp { args } {
    thaw [eval get_indices $args]
} "Thaw parameters with human syntax"

%proc untiep { args } {
    untie [eval get_indices $args]
} "Untie parameters with human syntax"

%proc mkAlbum { from to size {name spec} {ps 0} } {
    set chatter [tcloutr chatter]
    chatter 0
    set device [setplot device]
    setplot device /NULL
    set gcom [setcom WIN ALL]
    setcom GRID X $size,5
    while { [expr {$from + $size}] <= $to } {
        set until [expr {$from + $size}]
        set last [setcom R X $from  $until]
        plot
        setcom hardcopy $name$from-$until.ps/cps
        plot
        delete $last 2
        set from $until
    }
    delete $gcom
    set remain [expr {$to-$from}]
    if {$remain > 0} {
        set gcom [setcom WIN ALL]
        setcom GRID X $remain,5
        set until [expr {$from + $remain}]
        set last [setcom R X $from  $until]
        plot
        setcom hardcopy $name$from-$until.ps/cps
        plot
        delete $last 2
        delete $gcom 2
    }
    if { ! $ps } {
        foreach image [glob $name*.ps] { 
            exec ps2pdf $image 
            file delete $image 
        }
    }
    cpd $device
    eval chatter $chatter
}

%proc paramsToFile {fname {d ,} {all 0}} {
    set sp 10
    set cs 1
    set c  0
    set fstr "%8s %-8s $d %10.5g $d %10.5g $d %10.5g"
    with $fname w fd {
        puts $fd [format [regsub -all "\.5g" $fstr "s"] comp param value min max]
        for {set i 1} {$i <= [tcloutr modpar]} {incr i} {
            if { $i == $cs } { 
                incr c
                lassign [tcloutr comp $c] head cs cm
                set cs [expr {$cs+$cm}]
            }
            if { ! $all && [lindex [tcloutr error $i] 0] == [lindex [tcloutr error $i] 1]} continue
             
            puts $fd [format $fstr $head [string trim [tcloutr pinfo $i]] [lindex [tcloutr param $i] 0] \
                                         {*}[lrange [tcloutr error $i] 0 1]]
            set head ""
        }
    }
} "Write paramters and errors to file"

%proc parseArgs {args} {
    set current ""
    set rest {}
    foreach arg $args {
        if { "" != "$current" } {
            if { [string index $arg 0] == "-" } {
                throw "ArgErr" "-Flag argument following --argument with input."
            }
            uplevel set $current $arg
            set current ""
        } elseif { [string range $arg 0 1] == "--" } {
            set current [string range $arg 2 end]
        } elseif { [string index $arg 0] == "-" } {
            uplevel set [string range $arg 1 end] 1
        } else {
            lappend rest $arg
        }
    }
    return $rest
} "Argument parser"

eval namespace export [regsub {\s*} [xspec_commands::list_commands 0] " "]
}
#namespace xspec_commands
namespace import -force xspec_commands::*
mkallpshow

