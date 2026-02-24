set design [ed]
set lpp {M2 drawing}
set VIA12_DEF "VIA12"
set top3_a1 0.03
set bot3_a1 0.067
set top3_a2 0.067
set bot_3_a2 0.03
set common_terminal "S"
set filepath "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"
proc _get_source {} {
    set uniq [dict create]

    set insts [db::getInsts -of [ed]]
    db::foreach inst $insts {

        set sTerms ""
        catch { set sTerms [db::getInstTerms $::common_terminal -of $inst] }

        foreach sTerm $sTerms {

            set n ""
            catch { set n [db::getAttr net.name -of $sTerm] }

            # Skip empty
            if {$n eq ""} { continue }

            # Skip OA object handles
            if {[string match "oa:*" $n]} { continue }

            # Optional: also ensure it's not an object accidentally passed
            if {[regexp {^oa:0x} $n]} { continue }

            dict set uniq $n 1
        }
    }

    return [lsort [dict keys $uniq]]
}
proc _getShapesBbox {lpp} {
    set m2_shapes_all [db::getShapes -of [ed] -lpp $lpp -filter {%type=="Rect"}]
    set Bbox {}
    db::foreach shape $m2_shapes_all {
        set Bbox_of_metal [db::getAttr bBox -of $shape]
        lappend Bbox [list $shape $Bbox_of_metal]
    }
    set sortedBbox [lsort -index {1 1 1} -decreasing -real $Bbox]
    return $sortedBbox
}

proc _sortedMetals {sortedBbox} {
    set sorted {}
    foreach k $sortedBbox {
        set y1   [lindex $k 1 0 1]
        set y2   [lindex $k 1 1 1]
        set avg  [expr {($y1 + $y2)/2.0}]
        set x_ur [lindex $k 1 1 0]
        set x_ll [lindex $k 1 0 0]
        set obj  [lindex $k 0]
        lappend sorted [list $obj $x_ur $avg $x_ll]
    }
    return $sorted
}

proc _sortedRows {filepath} {
    set fh [open $filepath r]
    set uniq [dict create]   ;# acts like a set: key = Y value

    while {[gets $fh line] >= 0} {
        set line [string trim $line]
        if {$line eq ""} continue

        ;# skip comments and header-ish lines
        if {[string match "#*" $line]} continue
        if {[string match "INST_NAME*" $line]} continue

        ;# split by whitespace
        set cols [regexp -all -inline {\S+} $line]

        ;# need at least 7 columns:
        ;# 0:INST_NAME 1:ORIGIN_X 2:ORIGIN_Y 3:BBOX_LL_X 4:BBOX_LL_Y 5:BBOX_UR_X 6:BBOX_UR_Y
        if {[llength $cols] < 7} continue

        set ur_y [lindex $cols 6]

        ;# keep only numeric values (handles -2.423, 1.953, etc.)
        if {![string is double -strict $ur_y]} continue

        dict set uniq $ur_y 1
    }
    close $fh

    ;# unique keys, numeric sort, decreasing
    set ys [dict keys $uniq]
    return [lsort -real -decreasing $ys]
}

proc _createVia_search {rows sortedMetals VIA12_DEF } {
    set top3_a1  $::top3_a1
    set bot3_a1  $::bot3_a1
    set top3_a2  $::top3_a2
    set bot3_a2  $::bot_3_a2

    # Optional: skip first/last
    set rows         [lrange $rows 1 end-1]
    set sortedMetals [lrange $sortedMetals 1 end-1]

    set metal_idx 0
    set total [llength $sortedMetals]

    foreach row $rows {
        if {$metal_idx >= $total} break

        # ---------------------------
        # Decide offsets ONCE per row
        # ---------------------------
        set probeRec [lindex $sortedMetals $metal_idx]
        set probeXur [lindex $probeRec 1]
        set probeY   [lindex $probeRec 2]

        set probeX [expr {$probeXur - 0.03}]
        set probeV [le::createVia -design [ed] -definition $VIA12_DEF -origin [list $probeX $probeY] -orient R90]

        set hasNet 0
        set probeNetObj ""
        if {![catch {set probeNetObj [db::getAttr net -of $probeV]}]} {
            if {$probeNetObj ne ""} { set hasNet 1 }
        }
        catch {db::destroy $probeV}

        if {$hasNet} {
            set topOff $top3_a1
            set botOff $bot3_a1
            set topCount 3
            set botCount 2
        } else {
            set topOff $top3_a2
            set botOff $bot3_a2
            set topCount 2
            set botCount 3
        }

        # ---------------------------
        # TOP group (unchanged)
        # ---------------------------
        set off $topOff
        set list_names {}
        for {set m 0} {$m < $topCount} {incr m} {
            if {$metal_idx >= $total} break

            set rec   [lindex $sortedMetals $metal_idx]
            set mObj  [lindex $rec 0]
            set x_ur  [lindex $rec 1]
            set y_avg [lindex $rec 2]
            set x_ll  [lindex $rec 3]

            set x [expr {$x_ur - $off}]
            set named 0

            while {$x >= $x_ll} {
                set v [le::createVia -design [ed] -definition $VIA12_DEF -origin [list $x $y_avg] -orient R0]

                set netObj ""
                if {![catch {set netObj [db::getAttr net -of $v]}] && $netObj ne ""} {
                    set netName ""
                    catch {set netName [db::getAttr name -of $netObj]}

                    if {$netName eq "" || [lsearch -exact $list_names $netName] < 0} {
                        catch {db::setAttr net -of $mObj -value $netObj}
                        if {$netName ne ""} { lappend list_names $netName }
                        set named 1
                        catch {db::destroy $v}
                        break
                    }
                }

                catch {db::destroy $v}
                set x [expr {$x - 0.074}]
                db::setAttr net -of $mObj -value {}
            }

            if {!$named} { catch {db::destroy $mObj} }
            incr metal_idx
        }

        # ---------------------------
        # BOTTOM group (ONLY CHANGE HERE):
        # For m==0 or m==1: reject power/ground
        # ---------------------------
        set off $botOff
        set list_names {}
        for {set m 0} {$m < $botCount} {incr m} {
            if {$metal_idx >= $total} break

            set rec   [lindex $sortedMetals $metal_idx]
            set mObj  [lindex $rec 0]
            set x_ur  [lindex $rec 1]
            set y_avg [lindex $rec 2]
            set x_ll  [lindex $rec 3]

            set x [expr {$x_ur - $off}]
            set named 0

            while {$x >= $x_ll} {
                set v [le::createVia -design [ed] -definition $VIA12_DEF -origin [list $x $y_avg] -orient R0]

                set netObj ""
                if {![catch {set netObj [db::getAttr net -of $v]}] && $netObj ne ""} {

                    set netName ""
                    catch {set netName [db::getAttr name -of $netObj]}

                    # For the first TWO straps in bottom group, reject power/ground
                    # For the first TWO straps in bottom group, reject if netName is one of the source names
                        if {$m == 0 || $m == 1} {
                            set srcNames [_get_source]

                            if {[lsearch -exact $srcNames $netName] >= 0} {
                                puts "REJECT bottom strap m=$m metal_idx=$metal_idx netName='$netName' (in source list)"

                                catch {db::destroy $v}
                                set x [expr {$x - 0.074}]
                                db::setAttr net -of $mObj -value {}
                                continue
                            }
                        }
                    # Normal uniqueness rule (same as before)
                    if {$netName eq "" || [lsearch -exact $list_names $netName] < 0} {
                        catch {db::setAttr net -of $mObj -value $netObj}
                        if {$netName ne ""} { lappend list_names $netName }
                        set named 1
                        catch {db::destroy $v}
                        break
                    }
                }

                catch {db::destroy $v}
                set x [expr {$x - 0.074}]
                db::setAttr net -of $mObj -value {}
            }

            if {!$named} { catch {db::destroy $mObj} }
            incr metal_idx
        }
    }
}

proc _netname {lpp} {
    set v [db::getShapes -of [ed] -lpp $lpp -filter {%type=="Rect"}]
    set names {}

    db::foreach shape $v {
        if {![catch {set n [db::getAttr net.name -of $shape]}]} {
            lappend names $n
        }
    }
    return $names
}

set sortedBbox [_getShapesBbox $lpp]
set sorted    [_sortedMetals $sortedBbox]
set rows      [_sortedRows $filepath]

_createVia_search $rows $sorted $VIA12_DEF

set bBox [db::getAttr bBox -of $design]
de::select [db::getShapes -of [ed]]
le::autoVia -box $bBox -design $design