########################################################################
# extract_existing_m2_metals_with_net_from_report.tcl
#
# INPUT:
#   - REPORT_FILE: m2_grid_report.txt
#       lines like:  ... Yc=...  BB=(xll yll)-(xur yur)
#
# OUTPUT:
#   - OUT_FILE: formatted .txt listing ONLY metals that exist NOW in the design
#       plus their net names and coordinates.
#
# HOW IT WORKS:
#   - Parse report bboxes
#   - For each bbox, search design for an M2 Rect with matching bbox (within tol)
#   - If found: read net name from shape
#   - Write formatted text line using "format" (% params)
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set REPORT_FILE "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"
set OUT_FILE    "/home/users/svgplayout2601mofikry/gonna_work/current_m2_metals_with_nets.txt"

# LPP of the metals in your design
set LPP_M2 {M2 drawing}

# bbox match tolerance
set BBOX_TOL 0.0005

# ----------------------------
# HELPERS
# ----------------------------
proc isNumber {s} {
    return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc _tryGetNetName {obj} {
    if {$obj eq ""} { return "" }
    foreach expr {
        {db::getAttr net.name -of $obj}
        {db::getAttr netName  -of $obj}
        {db::getAttr net      -of $obj}
    } {
        set v ""
        if {![catch {set v [eval $expr]}]} {
            if {$v eq ""} { continue }
            if {[string match "oa:*" $v]} {
                set nm ""
                if {![catch {set nm [db::getAttr name -of $v]}]} {
                    if {$nm ne ""} { return $nm }
                }
            } else {
                return $v
            }
        }
    }
    return ""
}

proc _parseReportBBoxes {fname} {
    set fp [open $fname r]
    set out {}
    while {[gets $fp line] >= 0} {
        # Accept both:
        #   Yc=... BB=(xll yll)-(xur yur)
        # and lines without Yc but with BB=...
        if {[regexp {Yc=([-\d\.]+)\s+BB=\(([-\d\.]+)\s+([-\d\.]+)\)-\(([-\d\.]+)\s+([-\d\.]+)\)} \
                $line -> yc xll yll xur yur]} {
            lappend out [list $yc $xll $yll $xur $yur]
        } elseif {[regexp {BB=\(([-\d\.]+)\s+([-\d\.]+)\)-\(([-\d\.]+)\s+([-\d\.]+)\)} \
                $line -> xll yll xur yur]} {
            # yc unknown -> set to 0.0
            lappend out [list 0.0 $xll $yll $xur $yur]
        }
    }
    close $fp
    return $out
}

# Find an M2 Rect by bbox match
proc _findRectByBBox {design lpp xll yll xur yur tol} {
    set sh [db::getShapes -of $design -lpp $lpp -filter {%type=="Rect"}]
    db::foreach s $sh {
        set bb ""
        if {[catch {set bb [db::getAttr bBox -of $s]}]} { continue }

        set llx [lindex [lindex $bb 0] 0]
        set lly [lindex [lindex $bb 0] 1]
        set urx [lindex [lindex $bb 1] 0]
        set ury [lindex [lindex $bb 1] 1]

        if {abs($llx-$xll) < $tol && abs($lly-$yll) < $tol &&
            abs($urx-$xur) < $tol && abs($ury-$yur) < $tol} {
            return $s
        }
    }
    return ""
}

# ----------------------------
# MAIN
# ----------------------------
proc extract_existing_m2_metals_with_nets_from_report {} {
    set design [ed]
    if {$design eq ""} { error "No edit design ([ed]) found." }

    if {![file exists $::REPORT_FILE]} {
        error "REPORT_FILE not found: $::REPORT_FILE"
    }

    set items [_parseReportBBoxes $::REPORT_FILE]
    set n [llength $items]
    if {$n == 0} {
        error "No BB lines parsed from report: $::REPORT_FILE"
    }

    set fp [open $::OUT_FILE w]

    # Header (clean, aligned)
    puts $fp [format "%-6s %-24s %12s %12s %12s %12s %12s" \
        "IDX" "NET" "XLL" "YLL" "XUR" "YUR" "YC"]

    puts $fp [string repeat "-" 96]

    set kept 0
    set missing 0

    for {set i 0} {$i < $n} {incr i} {
        lassign [lindex $items $i] yc xll yll xur yur

        # Basic numeric sanity
        if {![isNumber $xll] || ![isNumber $yll] || ![isNumber $xur] || ![isNumber $yur]} {
            continue
        }

        set obj [_findRectByBBox $design $::LPP_M2 $xll $yll $xur $yur $::BBOX_TOL]
        if {$obj eq ""} {
            incr missing
            continue
        }

        set net [_tryGetNetName $obj]
        if {$net eq ""} { set net "NO_NET" }

        incr kept
        # Nicely aligned columns using format (% params)
        puts $fp [format "%-6d %-24s %12.6f %12.6f %12.6f %12.6f %12.6f" \
            $kept $net $xll $yll $xur $yur $yc]
    }

    puts $fp ""
    puts $fp [format "SUMMARY: kept=%d  missing_in_design=%d  parsed_from_report=%d" $kept $missing $n]
    close $fp

    puts "DONE: wrote $kept existing M2 metals to $::OUT_FILE (missing=$missing from report)"
}

# Run
extract_existing_m2_metals_with_nets_from_report

