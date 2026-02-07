
set lpp       {M2 drawing}
set VIA_DEF      "VIA12"
set STEP_X    0.074 
set starting_offset 0.03 

proc _get_nets_types_cordinates {lpp} {
    set k {}

    # Get rectangles; if it fails, treat as empty list
    if {[catch {set metals [db::getShapes -of [ed] -lpp $lpp -filter {%type=="Rect"}]}]} {
        set metals {}
    }

    db::foreach metal $metals {
        set signalType ""   ;# default when not available
        catch {set signalType [db::getAttr net.sigType -of $metal]}

        if {$signalType ne ""} {
            set coord ""
            catch {set coord [db::getAttr bBox -of $metal]}
            lappend k [list $metal $signalType $coord]
        }
        set sorted_k [lsort -index {2 1 1} -decreasing -real $k]
    }

    return $sorted_k
}

proc _filter_nets {nets_types_cordinates} {
    set k {}
    
    foreach item $nets_types_cordinates {
        set type [lindex $item 1]
        if {$type eq "power" || $type eq "ground"} {
            lappend k $item
        } 
    } 
    return $k
}

proc _taps_straps {lpp} {
    set shapes [db::getShapes -of [ed] -lpp $lpp -filter {%type=="Rect"}]
    set k {}
    db::foreach shape $shapes {
        set s [db::getAttr bBox -of $shape]
        lappend k [list $shape $s]
  }

  set sorted [lsort -index {1 1 1} -decreasing -real $k]
  set result [list [lindex $sorted 0] [lindex $sorted end]]
  return $result

}

proc _creat_vias12_taps {filter_nets taps_strap} {
    set upper_tap {}
    set lower_tap {}
    set lower_strap [lindex $taps_strap {1 1 1 1}]
    puts $lower_strap

    set uppr_strap [lindex $taps_strap {0 1 1 1}]
    puts $uppr_strap
    foreach net $filter_nets {
        set test_corr [lindex $net {2 1 1}]
        puts "upper_strap_y=<$uppr_strap> test_y=<$test_corr>"

        set answer [expr {$uppr_strap - $test_corr}]
        lappend upper_tap [list [list [lindex $net 0]] $answer]

    }
      foreach net $filter_nets {
        set test_corr [lindex $net {2 1 1}]

        set answer [expr {$lower_strap - $test_corr}]
        lappend lower_tap [list [list [lindex $net 0]]  $answer]

}
   
  set sorted_upper_tap [lsort -index {1} -increasing -real $upper_tap]
  set sorted_lower_tap [lsort -index {1} -decreasing -real $lower_tap]
  set upper_name  [lindex $sorted_upper_tap {0 0}]
  set lower_name  [lindex $sorted_lower_tap {0 0}]
  set upper_netObj_net [db::getAttr net -of $upper_name]
  set lower_netObj_net [db::getAttr net -of $lower_name]
  set upper_obj [lindex $taps_strap 0 0]
  set lower_obj [lindex $taps_strap 1 0]
  puts "$upper_obj"
  puts "$lower_obj"
  db::setAttr net -of $upper_obj -value $upper_netObj_net
  
  db::setAttr net -of $lower_obj -value $lower_netObj_net 
  

}
proc _edges_coord_after_naming {lpp} {
    set k [db::getShapes -of [ed] -lpp $lpp -filter {%type=="Rect"}]
    set new {}
    set i 0
    db::foreach shape $k {
        set bBox [db::getAttr bBox -of $shape]
        set y1 [lindex $bBox {0 1}]
        set y2 [lindex $bBox {1 1}]
        set avgY [expr {($y1 + $y2)/2.0}]
        set xUr [lindex $bBox {1 0}]
        set xLf [lindex $bBox {0 0}]
        
        lappend new [list $shape $xLf $xUr $avgY]
        
    }
    set sorted_new [lsort -index {3} -decreasing -real $new]
    
    set edges [list [lindex $sorted_new 0] [lindex $sorted_new end]]
    return $edges
}

proc _via12_placement {edges_coord_after_naming} {
    set point {}
    foreach edge  $edges_coord_after_naming {
        set start_offset $::starting_offset
        set xUr [lindex $edge 2 ]
        set xLf [lindex $edge 1 ]
        set shape [lindex $edge 0]
        set avgY [lindex $edge 3]
        set number_iter [expr {abs(($xUr - $xLf) / $::STEP_X)}]
        set x_start [expr {$xUr - $start_offset}]
        set point [list $x_start $avgY]
        le::createVia -definition $::VIA_DEF -design [ed] -origin $point
        set i 1
        while {$i <= $number_iter} {
            set x_start [expr {$x_start - $::STEP_X}]
            set point [list $x_start $avgY]

            le::createVia -definition $::VIA_DEF -design [ed] -origin $point
            incr i

        }

    }
}

set get_nets_types_cordinates [_get_nets_types_cordinates $lpp]
set filter_nets [_filter_nets $get_nets_types_cordinates]
set  taps_straps [_taps_straps $lpp]
_creat_vias12_taps $filter_nets $taps_straps
set edges_coord_after_naming [_edges_coord_after_naming $lpp]
_via12_placement $edges_coord_after_naming
