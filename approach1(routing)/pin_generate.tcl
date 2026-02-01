set cv [ed]
set shapes [db::getShapes -of $cv -lpp {M3 drawing}]

puts "Found [db::getCount $shapes] shapes on {M3 drawing}"

proc getPinsFromPinInfo {fname} {
    set fh [open $fname r]
    set pins {}

    while {[gets $fh line] >= 0} {
        if {[regexp {^\*\.PININFO\s+(.*)$} $line -> rest]} {
            foreach tok [split $rest] {
                set pin [lindex [split $tok ":"] 0]
                lappend pins $pin
            }
            break
        }
    }
    close $fh
    return $pins
}

set pins [getPinsFromPinInfo "/home/users/svgplayout2601mofikry/gonna_work/netlist.txt"]
puts $pins


db::foreach s $shapes {
  set i 0

    # bbox = {{xl yl} {xh yh}}
    set bb [db::getAttr bBox -of $s]
    set ll [lindex $bb 0]
    set ur [lindex $bb 1]

    set xc [expr {([lindex $ll 0] + [lindex $ur 0]) / 2.0}]
    set yc [expr {([lindex $ll 1] + [lindex $ur 1]) / 2.0}]

    # Get net name
    set txt ""
    catch {
        set txt [db::getAttr net.name -of $s]
    }

    if {$txt eq ""} {
        continue
    }
  foreach k $pins {
    
       
  if {$txt != [lindex $pins $i]} { 
incr i
} else {
    # Create label
    le::createLabel $txt \
        -parent $cv \
        -lpp {M3 text} \
        -origin [list $xc $yc] \
        -just centerCenter \
        -orient R0 \
        -height 0.3
 break
}
}
}
le::createPinsFromText -design $design

