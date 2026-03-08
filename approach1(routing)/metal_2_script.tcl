########################################################################
# SHARING CONFIGURATION
########################################################################

set sharing                 "s"
set sharing_distance        0.12
set sharing_x_offset        0.093
set sharing_y_offset        0.055
set sharing_y_offset_MX     0.5

########################################################################
# METAL SETTINGS
########################################################################

set lpp        {M2 drawing}
set m2_width   0.034
set min_gap    0.034
########################################################################
# DRAIN SHARING
########################################################################

set sharing_x_offset_list       {0.167 0.167 0.167}
set sharing_y_offset_list       {0.115 0.175 0.235}
set drain_min_gap               0.034
set drain_sharing_y_offsets_MX  {0.440 0.38 0.320}

########################################################################
# GATE SHARING
########################################################################

set gate_sharing_x_offsets      {0.13 0.13 0.13}
set gate_sharing_y_offsets      {0.366 0.426 0.486}
set gate_distance               0.12
set gate_min_gap                0.034
set gate_sharing_y_offsets_MX   {0.044 0.104 0.164}

##############################################################################

set open_lane2_thresh 0.6
set strap_max_len     2.7

############################################################
# _get_bBox
############################################################
proc _get_bBox {} {
    set design [ed]
    set insts [db::getInsts -of $design]
    set my_list {}

    db::foreach inst $insts {
        set is_mos 0
        catch {
            set cellName [db::getAttr cellName -of $inst]
            if {[string match -nocase "*pfet*" $cellName] ||
                [string match -nocase "*nfet*" $cellName]} {
                set is_mos 1
            }
        }
        if {!$is_mos} { continue }

        set box    [db::getAttr bBox -of $inst]
        set source [db::getInstTerms S -of $inst]
        set drain  [db::getInstTerms D -of $inst]
        set gate   [db::getInstTerms G -of $inst]
        set s_name [db::getAttr net.name -of $source]
        set d_name [db::getAttr net.name -of $drain]
        set g_name [db::getAttr net.name -of $gate]

        lappend my_list [list $inst $box \
            [list s $s_name] [list d $d_name] [list g $g_name]]
    }

    set sorted_list [lsort -index {1 1 1} -real -decreasing $my_list]
    if {[llength $sorted_list] == 0} { return {} }

    set grouped_list {}
    set current_row  {}
    set last_y       ""

    foreach item $sorted_list {
        set current_y [lindex $item 1 1 1]
        if {$current_y != $last_y && $last_y != ""} {
            lappend grouped_list \
                [lsort -index {1 1 0} -real -decreasing $current_row]
            set current_row {}
        }
        lappend current_row $item
        set last_y $current_y
    }

    if {[llength $current_row] > 0} {
        lappend grouped_list \
            [lsort -index {1 1 0} -real -decreasing $current_row]
    }

    return $grouped_list
}

############################################################
# _gonna_make_metal_2
############################################################
proc _gonna_make_metal_2 {get_bBox} {
    foreach row $get_bBox {

        if {[llength $row] == 0} {
            continue
        }

        set inst  [lindex $row 0 0]
        set tra   [db::getAttr transform -of $inst]
        set orien [db::getAttr orient    -of $tra]

        if {$orien == "R0" || $orien == "MY"} {
            set sharing_y_offset $::sharing_y_offset
        } elseif {$orien == "MX" || $orien == "R180"} {
            set sharing_y_offset $::sharing_y_offset_MX
        }

        # row edges exactly like your drain-style expansion idea
        set row_xur [lindex [lindex $row 0]   1 1 0]
        set row_xll [lindex [lindex $row end] 1 0 0]

        set i 0
        set k [llength $row]
        set n 0

        while {$i < $k} {
            set net1 [lindex $row $i 2 1]

            if {$n == 0} {
                set group_start_i $i
                set inst_box  [lindex $row $i 1]
                set xur_start [lindex $inst_box 1 0]
                set xur_end   $xur_start
                set n 1
            }

            if {$i == ($k-1)} {
                set net2 "__END__"
            } else {
                set net2 [lindex $row [expr {$i+1}] 2 1]
            }

            if {$net1 == $net2} {
                set next_box [lindex $row [expr {$i+1}] 1]
                set xur_end  [lindex $next_box 1 0]
                incr i
            } else {
                set ur_pt  [lindex $inst_box 1]
                set y_ur   [expr {[lindex $ur_pt 1] - $sharing_y_offset}]
                set x_ur   [expr {[lindex $ur_pt 0] - $::sharing_x_offset}]

                set span_x [expr {$xur_start - $xur_end}]
                set length [expr {$span_x + $::sharing_distance}]

                set gap         $::drain_min_gap
                set cur_ur_x    $x_ur
                set ur_y        $y_ur
                set ll_target_x [expr {$cur_ur_x - $length}]

                # ------------------------------------------------
                # corner expansion: same idea as _extend_spans
                # ------------------------------------------------

                # first group in row -> extend UR to row_xur
                if {$group_start_i == 0} {
                    set new_ur $row_xur
                    if {[expr {$new_ur - $ll_target_x}] > $::strap_max_len} {
                        set new_ur [expr {$ll_target_x + $::strap_max_len}]
                    }
                    if {$new_ur > $cur_ur_x} {
                        set cur_ur_x $new_ur
                    }
                }

                # last group in row -> extend LL to row_xll
                if {$i == ($k-1)} {
                    set new_ll $row_xll
                    if {[expr {$cur_ur_x - $new_ll}] > $::strap_max_len} {
                        set new_ll [expr {$cur_ur_x - $::strap_max_len}]
                    }
                    if {$new_ll < $ll_target_x} {
                        set ll_target_x $new_ll
                    }
                }

                while {1} {
                    set cur_ll_x [expr {$cur_ur_x - $::strap_max_len}]
                    if {$cur_ll_x <= $ll_target_x} {
                        set last_len [expr {$cur_ur_x - $ll_target_x}]
                        if {$last_len > 0} {
                            set y_ll [expr {$ur_y - $::m2_width}]
                            set box  [list [list $ll_target_x $y_ll] \
                                           [list $cur_ur_x   $ur_y]]
                            le::createRectangle $box -design [ed] \
                                -lpp $::lpp -net $net1
                        }
                        break
                    } else {
                        set y_ll [expr {$ur_y - $::m2_width}]
                        set box  [list [list $cur_ll_x $y_ll] \
                                       [list $cur_ur_x $ur_y]]
                        le::createRectangle $box -design [ed] \
                            -lpp $::lpp -net $net1
                        set cur_ur_x [expr {$cur_ll_x - $gap}]
                        if {$cur_ur_x <= $ll_target_x} { break }
                    }
                }

                set n 0
                incr i
            }
        }
    }
}
############################################################
# HELPER
############################################################
proc _run_base_len {first_ur last_ur trim} {
    expr {$first_ur - ($last_ur - $trim)}
}

############################################################
# HELPER:
# Pick lane for a net using your clarified rule
#
# Rule:
#   1) Search all open lanes.
#   2) If a lane's LAST net == current net, reuse that lane.
#      If multiple match, choose the most recently used lane.
#   3) If none match, use round-robin lane.
#   4) While using only 2 lanes, lane-2 can open if the chosen
#      round-robin lane currently has a short last run.
############################################################
proc _pick_lane_for_net {net1 lanes_in_use next_lane span_thresh lane_last_net_name lane_last_order_name lane_runs_name} {
    upvar 1 $lane_last_net_name lane_last_net
    upvar 1 $lane_last_order_name lane_last_order
    upvar 1 $lane_runs_name lane_runs

    # -----------------------------------
    # Step 1: find matching lane(s)
    # -----------------------------------
    set found_lane -1
    set best_order -1

    for {set L 0} {$L < $lanes_in_use} {incr L} {
        if {[info exists lane_last_net($L)] && $lane_last_net($L) eq $net1} {
            set ord -1
            if {[info exists lane_last_order($L)]} {
                set ord $lane_last_order($L)
            }
            if {$ord > $best_order} {
                set best_order $ord
                set found_lane $L
            }
        }
    }

    if {$found_lane != -1} {
        return [list $found_lane $lanes_in_use]
    }

    # -----------------------------------
    # Step 2: no matching lane -> round robin
    # -----------------------------------
    set L $next_lane

    # open lane 2 only when we are still using 2 lanes
    if {$lanes_in_use == 2 && [llength $lane_runs($L)] > 0} {
        set last_run [lindex $lane_runs($L) end]
        set s [lindex $last_run 1]
        set e [lindex $last_run 2]
        if {[expr {$s - $e}] < $span_thresh} {
            set lanes_in_use 3
            set L 2
        }
    }

    return [list $L $lanes_in_use]
}

############################################################
# _extend_spans
############################################################
proc _extend_spans {ns_var nl_var row_xur row_xll gap} {
    upvar 1 $ns_var net_span
    upvar 1 $nl_var net_lane

    set meet_gap 0.026
    set max_len  2.7

    # Pass A: proportional extension between neighbors until they meet (gap = 0.026)
    for {set L 0} {$L < 3} {incr L} {

        set tagged {}
        foreach nn [array names net_lane] {
            if {$net_lane($nn) == $L && [info exists net_span($nn)]} {
                lappend tagged [list [lindex $net_span($nn) 0] $nn]
            }
        }
        if {[llength $tagged] < 2} { continue }
        set tagged [lsort -real -decreasing -index 0 $tagged]

        set lane_nets {}
        foreach t $tagged {
            lappend lane_nets [lindex $t 1]
        }

        set N [llength $lane_nets]
        for {set p 0} {$p < ($N-1)} {incr p} {
            set nr [lindex $lane_nets $p]
            set nl [lindex $lane_nets [expr {$p+1}]]

            set ur_r [lindex $net_span($nr) 0]
            set ll_r [lindex $net_span($nr) 1]
            set y_r  [lindex $net_span($nr) 2]

            set ur_l [lindex $net_span($nl) 0]
            set ll_l [lindex $net_span($nl) 1]
            set y_l  [lindex $net_span($nl) 2]

            # Total space between left edge of right span and right edge of left span
            # free_space = how much we can consume until only meet_gap remains
            set free_space [expr {$ll_r - $ur_l - $meet_gap}]
            if {$free_space <= 0} { continue }

            set len_r [expr {$ur_r - $ll_r}]
            set len_l [expr {$ur_l - $ll_l}]
            set denom [expr {$len_r + $len_l}]

            if {$denom <= 0} {
                # Equal split if both have zero length
                set ext_r [expr {$free_space / 2.0}]
                set ext_l [expr {$free_space / 2.0}]
            } else {
                # Longer metal extends less, shorter metal extends more
                # ext_r is proportional to len_l (opposite), so shorter gets more room
                set ext_r [expr {$free_space * $len_l / double($denom)}]
                set ext_l [expr {$free_space * $len_r / double($denom)}]
            }

            # --------------------------------------------------
            # Apply cap rule:
            # 1) if current length >= 2.7 -> no extension
            # 2) otherwise extension is capped so final length <= 2.7
            # --------------------------------------------------

            # Right span grows leftward (ll_r shrinks)
            if {$len_r >= $max_len} {
                set ext_r 0
            } else {
                set allowed_r [expr {$max_len - $len_r}]
                if {$ext_r > $allowed_r} {
                    set ext_r $allowed_r
                }
            }

            # Left span grows rightward (ur_l grows)
            if {$len_l >= $max_len} {
                set ext_l 0
            } else {
                set allowed_l [expr {$max_len - $len_l}]
                if {$ext_l > $allowed_l} {
                    set ext_l $allowed_l
                }
            }

            # Update spans
            if {$ext_r > 0} {
                set net_span($nr) [list $ur_r [expr {$ll_r - $ext_r}] $y_r]
            }
            if {$ext_l > 0} {
                set net_span($nl) [list [expr {$ur_l + $ext_l}] $ll_l $y_l]
            }
        }
    }

    # Pass B: extend outermost nets to row edges
    for {set L 0} {$L < 3} {incr L} {

        set tagged {}
        foreach nn [array names net_lane] {
            if {$net_lane($nn) == $L && [info exists net_span($nn)]} {
                lappend tagged [list [lindex $net_span($nn) 0] $nn]
            }
        }
        if {[llength $tagged] == 0} { continue }
        set tagged [lsort -real -decreasing -index 0 $tagged]

        # Rightmost span -> extend UR toward row_xur
        set rightmost [lindex [lindex $tagged 0] 1]
        set ur_r [lindex $net_span($rightmost) 0]
        set ll_r [lindex $net_span($rightmost) 1]
        set y_r  [lindex $net_span($rightmost) 2]
        set len_r [expr {$ur_r - $ll_r}]

        if {$len_r < $max_len} {
            set new_ur $row_xur
            if {[expr {$new_ur - $ll_r}] > $max_len} {
                set new_ur [expr {$ll_r + $max_len}]
            }
            if {$new_ur > $ur_r} {
                set net_span($rightmost) [list $new_ur $ll_r $y_r]
            }
        }

        # Leftmost span -> extend LL toward row_xll
        set leftmost [lindex [lindex $tagged end] 1]
        set ur_l [lindex $net_span($leftmost) 0]
        set ll_l [lindex $net_span($leftmost) 1]
        set y_l  [lindex $net_span($leftmost) 2]
        set len_l [expr {$ur_l - $ll_l}]

        if {$len_l < $max_len} {
            set new_ll $row_xll
            if {[expr {$ur_l - $new_ll}] > $max_len} {
                set new_ll [expr {$ur_l - $max_len}]
            }
            if {$new_ll < $ll_l} {
                set net_span($leftmost) [list $ur_l $new_ll $y_l]
            }
        }
    }
}
############################################################
# _gonna_make_drain
############################################################
proc _gonna_make_drain {get_bBox {do_extend 0}} {

    set kk          {}
    set span_thresh 0.6
    set trim        0.034
    set min_gap     $::min_gap

    foreach row $get_bBox {

        for {set L 0} {$L < 3} {incr L} {
            set lane_enhance($L) {}
        }

        set k [llength $row]
        if {$k == 0} {
            lappend kk {}
            continue
        }

        set inst0  [lindex $row 0 0]
        set tra0   [db::getAttr transform -of $inst0]
        set orien0 [db::getAttr orient    -of $tra0]

        if {$orien0 == "MX" || $orien0 == "R180"} {
            set y_offset_list $::drain_sharing_y_offsets_MX
        } else {
            set y_offset_list $::sharing_y_offset_list
        }

        set lanes_in_use 2
        set next_lane    0
        set i            0
        set run_order    0

        set row_xur [lindex [lindex $row 0]   1 1 0]
        set row_xll [lindex [lindex $row end] 1 0 0]

        array unset lane_last_net
        array unset lane_last_order
        array unset lane_runs

        for {set L 0} {$L < 3} {incr L} {
            set lane_last_net($L)   ""
            set lane_last_order($L) -1
            set lane_runs($L)       {}
        }

        # PASS 1: build runs with corrected lane assignment
        while {$i < $k} {

            set inst [lindex $row $i 0]
            set is_dummy 0
            catch { set is_dummy [db::getAttr dummy -of $inst] }
            if {$is_dummy} {
                incr i
                continue
            }

            set net1     [lindex $row $i 3 1]
            set inst_box [lindex $row $i 1]
            set dev_xur  [lindex $inst_box 1 0]
            set dev_yur  [lindex $inst_box 1 1]

            lassign [_pick_lane_for_net $net1 $lanes_in_use $next_lane $span_thresh \
                lane_last_net lane_last_order lane_runs] L lanes_in_use

            set x_off [lindex $::sharing_x_offset_list $L]
            set y_off [lindex $y_offset_list $L]

            set ur_x  [expr {$dev_xur - $x_off}]
            set ll_x  [expr {$ur_x - $trim}]
            set run_y [expr {$dev_yur - $y_off}]

            incr i
            while {$i < $k} {
                set inst2 [lindex $row $i 0]
                set is_dummy2 0
                catch { set is_dummy2 [db::getAttr dummy -of $inst2] }
                if {$is_dummy2} {
                    incr i
                    continue
                }

                set net2 [lindex $row $i 3 1]
                if {$net2 ne $net1} { break }

                set inst_box2 [lindex $row $i 1]
                set dev2_xur  [lindex $inst_box2 1 0]
                set ll_x [expr {$dev2_xur - $x_off - $trim}]
                incr i
            }

            lappend lane_runs($L) [list $net1 $ur_x $ll_x $run_y]
            set lane_last_net($L)   $net1
            set lane_last_order($L) $run_order
            incr run_order

            incr next_lane
            if {$next_lane >= $lanes_in_use} {
                set next_lane 0
            }
        }

        # PASS 2: merge consecutive same-net runs in each lane
        set gap $::drain_min_gap

        array unset net_span
        array unset net_lane

        for {set L 0} {$L < 3} {incr L} {
            set runs $lane_runs($L)
            set nr   [llength $runs]
            if {$nr == 0} { continue }

            set merged {}
            set cur_run [lindex $runs 0]

            for {set r 1} {$r < $nr} {incr r} {
                set next_run [lindex $runs $r]
                if {[lindex $next_run 0] eq [lindex $cur_run 0]} {
                    set cur_run [list \
                        [lindex $cur_run 0] \
                        [lindex $cur_run 1] \
                        [lindex $next_run 2] \
                        [lindex $cur_run 3]]
                } else {
                    lappend merged $cur_run
                    set cur_run $next_run
                }
            }
            lappend merged $cur_run

            set idx 0
            foreach run $merged {
                set net  [lindex $run 0]
                set ur_x [lindex $run 1]
                set ll_x [lindex $run 2]
                set y    [lindex $run 3]
                set key  "${net}:${L}:${idx}"
                set net_span($key) [list $ur_x $ll_x $y]
                set net_lane($key) $L
                incr idx
            }
        }

        if {$do_extend} {
            _extend_spans net_span net_lane $row_xur $row_xll $gap
        }

        # PASS 3: split spans into chunks
        for {set L 0} {$L < 3} {incr L} {
            set lane_segs($L) {}
        }

        foreach key [array names net_span] {
            set L     $net_lane($key)
            set ur_x  [lindex $net_span($key) 0]
            set ll_x  [lindex $net_span($key) 1]
            set run_y [lindex $net_span($key) 2]
            set net   [lindex [split $key :] 0]

            set cur_ur $ur_x
            while {1} {
                set cur_ll [expr {$cur_ur - $::strap_max_len}]
                if {$cur_ll <= $ll_x} {
                    set last_len [expr {$cur_ur - $ll_x}]
                    if {$last_len > 0} {
                        lappend lane_segs($L) [list $net $cur_ur $run_y $last_len]
                    }
                    break
                }
                lappend lane_segs($L) [list $net $cur_ur $run_y $::strap_max_len]
                set cur_ur [expr {$cur_ll - $gap}]
                if {$cur_ur <= $ll_x} { break }
            }
        }

        # PASS 4: create rectangles
        for {set L 0} {$L < 3} {incr L} {
            foreach seg $lane_segs($L) {
                set net    [lindex $seg 0]
                set ur_x   [lindex $seg 1]
                set ur_y   [lindex $seg 2]
                set length [lindex $seg 3]

                set x_ll [expr {$ur_x - $length}]
                set y_ll [expr {$ur_y - $::m2_width}]
                set box  [list [list $x_ll $y_ll] [list $ur_x $ur_y]]

                set rect [le::createRectangle $box -design [ed] -lpp $::lpp -net $net]
                lappend lane_enhance($L) [list $orien0 $rect $box $net]
            }
        }

        set enhance_list {}
        for {set L 0} {$L < $lanes_in_use} {incr L} {
            lappend enhance_list $lane_enhance($L)
        }
        lappend kk $enhance_list
    }

    return $kk
}

############################################################
# _gonna_make_gate
############################################################
proc _gonna_make_gate {get_bBox {do_extend 0}} {

    set kk          {}
    set span_thresh 0.6
    set trim        0.108
    set min_gap     $::min_gap

    foreach row $get_bBox {

        for {set L 0} {$L < 3} {incr L} {
            set lane_enhance($L) {}
        }

        set k [llength $row]
        if {$k == 0} {
            lappend kk {}
            continue
        }

        set inst0  [lindex $row 0 0]
        set tra0   [db::getAttr transform -of $inst0]
        set orien0 [db::getAttr orient    -of $tra0]

        if {$orien0 == "MX" || $orien0 == "R180"} {
            set y_offset_list $::gate_sharing_y_offsets_MX
        } else {
            set y_offset_list $::gate_sharing_y_offsets
        }

        set lanes_in_use 2
        set next_lane    0
        set i            0
        set run_order    0

        set row_xur [lindex [lindex $row 0]   1 1 0]
        set row_xll [lindex [lindex $row end] 1 0 0]

        array unset lane_last_net
        array unset lane_last_order
        array unset lane_runs

        for {set L 0} {$L < 3} {incr L} {
            set lane_last_net($L)   ""
            set lane_last_order($L) -1
            set lane_runs($L)       {}
        }

        # PASS 1: build runs with corrected lane assignment
        while {$i < $k} {

            set inst [lindex $row $i 0]
            set is_dummy 0
            catch { set is_dummy [db::getAttr dummy -of $inst] }
            if {$is_dummy} {
                incr i
                continue
            }

            set net1     [lindex $row $i 4 1]
            set inst_box [lindex $row $i 1]
            set dev_xur  [lindex $inst_box 1 0]
            set dev_yur  [lindex $inst_box 1 1]

            lassign [_pick_lane_for_net $net1 $lanes_in_use $next_lane $span_thresh \
                lane_last_net lane_last_order lane_runs] L lanes_in_use

            set x_off [lindex $::gate_sharing_x_offsets $L]
            set y_off [lindex $y_offset_list $L]

            set ur_x  [expr {$dev_xur - $x_off}]
            set ll_x  [expr {$ur_x - $trim}]
            set run_y [expr {$dev_yur - $y_off}]

            incr i
            while {$i < $k} {
                set inst2 [lindex $row $i 0]
                set is_dummy2 0
                catch { set is_dummy2 [db::getAttr dummy -of $inst2] }
                if {$is_dummy2} {
                    incr i
                    continue
                }

                set net2 [lindex $row $i 4 1]
                if {$net2 ne $net1} { break }

                set inst_box2 [lindex $row $i 1]
                set dev2_xur  [lindex $inst_box2 1 0]
                set ll_x [expr {$dev2_xur - $x_off - $trim}]
                incr i
            }

            lappend lane_runs($L) [list $net1 $ur_x $ll_x $run_y]
            set lane_last_net($L)   $net1
            set lane_last_order($L) $run_order
            incr run_order

            incr next_lane
            if {$next_lane >= $lanes_in_use} {
                set next_lane 0
            }
        }

        # PASS 2: merge consecutive same-net runs in each lane
        set gap $::gate_min_gap

        array unset net_span
        array unset net_lane

        for {set L 0} {$L < 3} {incr L} {
            set runs $lane_runs($L)
            set nr   [llength $runs]
            if {$nr == 0} { continue }

            set merged {}
            set cur_run [lindex $runs 0]

            for {set r 1} {$r < $nr} {incr r} {
                set next_run [lindex $runs $r]
                if {[lindex $next_run 0] eq [lindex $cur_run 0]} {
                    set cur_run [list \
                        [lindex $cur_run 0] \
                        [lindex $cur_run 1] \
                        [lindex $next_run 2] \
                        [lindex $cur_run 3]]
                } else {
                    lappend merged $cur_run
                    set cur_run $next_run
                }
            }
            lappend merged $cur_run

            set idx 0
            foreach run $merged {
                set net  [lindex $run 0]
                set ur_x [lindex $run 1]
                set ll_x [lindex $run 2]
                set y    [lindex $run 3]
                set key  "${net}:${L}:${idx}"
                set net_span($key) [list $ur_x $ll_x $y]
                set net_lane($key) $L
                incr idx
            }
        }

        if {$do_extend} {
            _extend_spans net_span net_lane $row_xur $row_xll $gap
        }

        # PASS 3: split spans into chunks
        for {set L 0} {$L < 3} {incr L} {
            set lane_segs($L) {}
        }

        foreach key [array names net_span] {
            set L     $net_lane($key)
            set ur_x  [lindex $net_span($key) 0]
            set ll_x  [lindex $net_span($key) 1]
            set run_y [lindex $net_span($key) 2]
            set net   [lindex [split $key :] 0]

            set cur_ur $ur_x
            while {1} {
                set cur_ll [expr {$cur_ur - $::strap_max_len}]
                if {$cur_ll <= $ll_x} {
                    set last_len [expr {$cur_ur - $ll_x}]
                    if {$last_len > 0} {
                        lappend lane_segs($L) [list $net $cur_ur $run_y $last_len]
                    }
                    break
                }
                lappend lane_segs($L) [list $net $cur_ur $run_y $::strap_max_len]
                set cur_ur [expr {$cur_ll - $gap}]
                if {$cur_ur <= $ll_x} { break }
            }
        }

        # PASS 4: create rectangles
        for {set L 0} {$L < 3} {incr L} {
            foreach seg $lane_segs($L) {
                set net    [lindex $seg 0]
                set ur_x   [lindex $seg 1]
                set ur_y   [lindex $seg 2]
                set length [lindex $seg 3]

                set x_ll [expr {$ur_x - $length}]
                set y_ll [expr {$ur_y - $::m2_width}]
                set box  [list [list $x_ll $y_ll] [list $ur_x $ur_y]]

                set rect [le::createRectangle $box -design [ed] -lpp $::lpp -net $net]
                lappend lane_enhance($L) [list $orien0 $rect $box $net]
            }
        }

        set enhance_list {}
        for {set L 0} {$L < $lanes_in_use} {incr L} {
            lappend enhance_list $lane_enhance($L)
        }
        lappend kk $enhance_list
    }

    return $kk
}

############################################################
# _enhance
############################################################
proc _enhance {drain_list gate_list} {
    foreach row $drain_list {
        set num_lanes [llength $row]
        if {$num_lanes > 2} {
            continue
        }

        set recreate_list {}

        # ---------------------------------
        # First pass: collect new boxes from lane 0 and lane 1
        # ---------------------------------
        set lane_idx 0
        foreach lane $row {
            if {$lane_idx > 1} { break }

            set step [expr {$lane_idx + 1}]
            foreach strap $lane {
                set orient [lindex $strap 0]
                set inst   [lindex $strap 1]
                set bBox   [lindex $strap 2]
                set net    [lindex $strap 3]

                if {$inst eq ""} { continue }

                set xll [lindex $bBox 0 0]
                set yll [lindex $bBox 0 1]
                set xur [lindex $bBox 1 0]
                set yur [lindex $bBox 1 1]

                if {$orient == "R0" || $orient == "MY"} {
                    set yur [expr {$yur - $step*0.034}]
                    set yll [expr {$yll - $step*0.034}]
                } else {
                    set yur [expr {$yur + $step*0.034}]
                    set yll [expr {$yll + $step*0.034}]
                }

                set new_box [list [list $xll $yll] [list $xur $yur]]
                lappend recreate_list [list $inst $new_box $net]
            }

            incr lane_idx
        }

        # ---------------------------------
        # Second pass: delete all metals in lane 0 and 1
        # ---------------------------------
        foreach item $recreate_list {
            set inst [lindex $item 0]
            if {$inst ne ""} {
                db::destroy $inst
            }
        }

        # ---------------------------------
        # Third pass: recreate all metals with new bBoxes
        # ---------------------------------
        foreach item $recreate_list {
            set new_box [lindex $item 1]
            set net     [lindex $item 2]
            le::createRectangle $new_box -design [ed] -lpp $::lpp -net $net
        }
    }

    foreach row $gate_list {
        set num_lanes [llength $row]
        if {$num_lanes > 2} {
            continue
        }

        set recreate_list {}

        # ---------------------------------
        # First pass: collect new boxes from lane 0 and lane 1
        # ---------------------------------
        set lane_idx 0
        foreach lane $row {
            if {$lane_idx > 1} { break }

            set step [expr {$lane_idx + 1}]
            foreach strap $lane {
                set orient [lindex $strap 0]
                set inst   [lindex $strap 1]
                set bBox   [lindex $strap 2]
                set net    [lindex $strap 3]

                if {$inst eq ""} { continue }

                set xll [lindex $bBox 0 0]
                set yll [lindex $bBox 0 1]
                set xur [lindex $bBox 1 0]
                set yur [lindex $bBox 1 1]

                set yur [expr {$yur - $step*0.034}]
                set yll [expr {$yll - $step*0.034}]

                set new_box [list [list $xll $yll] [list $xur $yur]]
                lappend recreate_list [list $inst $new_box $net]
            }

            incr lane_idx
        }

        # ---------------------------------
        # Second pass: delete all metals in lane 0 and 1
        # ---------------------------------
        foreach item $recreate_list {
            set inst [lindex $item 0]
            if {$inst ne ""} {
                db::destroy $inst
            }
        }

        # ---------------------------------
        # Third pass: recreate all metals with new bBoxes
        # ---------------------------------
        foreach item $recreate_list {
            set new_box [lindex $item 1]
            set net     [lindex $item 2]
            le::createRectangle $new_box -design [ed] -lpp $::lpp -net $net
        }
    }
}
############################################################
# MAIN
############################################################
set get_bBox [_get_bBox]
_gonna_make_metal_2 $get_bBox
set enhance_drain [_gonna_make_drain $get_bBox 1]
set enhance_gate  [_gonna_make_gate  $get_bBox 1]
_enhance $enhance_drain $enhance_gate