########################################################################
# place_m3_by_unique_nets_from_m2_txt.tcl  (EDITED: always full OTA height)
#
# INPUT:
#   IN_M2_FILE: formatted txt like:
#     IDX NET XLL YLL XUR YUR YC
#   (header lines + dashed line + SUMMARY)
#
#   IN_OTA_FILE: your "1_st_op" txt containing:
#     # OTA_BOTTOM_LEFT = (x, y)
#     # OTA_TOP_RIGHT   = (x, y)
#
# OUTPUT:
#   OUT_M3_FILE: formatted txt listing created M3 rectangles
#
# PLACEMENT RULES (edited):
#   - One M3 per UNIQUE net (remove duplicates)
#   - Compute total M2 width from global min(XLL) and max(XUR)
#   - Horizontal spacing dx = M2_width / numUniqueNets
#   - Assign each net a unique Xc = XLL_min + (k+0.5)*dx
#   - IMPORTANT CHANGE:
#       * ALL M3 pillars span the FULL OTA height:
#           y1 = otaYBL, y2 = otaYTR
#       * Removed stub/multi-span/min-length/extension logic
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set IN_M2_FILE  "/home/users/svgplayout2601mofikry/gonna_work/current_m2_metals_with_nets.txt"
set OUT_M3_FILE "/home/users/svgplayout2601mofikry/gonna_work/m3_coords.txt"

# OTA bbox source (your "1_st_op" txt)
set IN_OTA_FILE "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"

# M3 layer
set LPP_M3 {M3 drawing}

# Width of each M3 pillar (absolute, in X)
set M3_WIDTH 0.04

# Skip nets named NO_NET if present
set SKIP_NO_NET 1

# ----------------------------
# HELPERS
# ----------------------------
proc isNumber {s} {
    # supports regular decimals only (matches your file format)
    return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc _getEditDesign {} {
    set ctx [de::getActiveContext]
    if {$ctx eq ""} { return "" }
    set d ""
    catch { set d [db::getAttr editDesign -of $ctx] }
    return $d
}

proc _readM2DumpFile {fname} {
    # returns list of records: {net xll yll xur yur yc}
    set fp [open $fname r]
    set recs {}

    while {[gets $fp line] >= 0} {
        set line [string trim $line]
        if {$line eq ""} { continue }
        if {[string match "IDX*" $line]} { continue }
        if {[string match "-----*" $line]} { continue }
        if {[string match "SUMMARY:*" $line]} { continue }

        # Data line format:
        # idx net xll yll xur yur yc
        if {[regexp {^\s*([0-9]+)\s+(\S+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s*$} \
                $line -> idx net xll yll xur yur yc]} {

            if {![isNumber $xll] || ![isNumber $yll] || ![isNumber $xur] || ![isNumber $yur] || ![isNumber $yc]} {
                continue
            }
            lappend recs [list $net $xll $yll $xur $yur $yc]
        }
    }

    close $fp
    return $recs
}

proc _openOutTxt {fname} {
    set fp [open $fname w]
    puts $fp [format "%-6s %-24s %12s %12s %12s %12s %12s %12s %10s" \
        "IDX" "NET" "XLL" "YLL" "XUR" "YUR" "Xc" "Yspan" "dxSlot"]
    puts $fp [string repeat "-" 130]
    return $fp
}

proc _readOtaBBox {fname} {
    # Parses OTA_BOTTOM_LEFT and OTA_TOP_RIGHT from your 1_st_op file.
    # Returns list: {otaYBL otaYTR}
    if {![file exists $fname]} {
        error "IN_OTA_FILE not found: $fname"
    }
    set fp [open $fname r]
    set yBL ""
    set yTR ""
    while {[gets $fp line] >= 0} {
        set line [string trim $line]
        # Example lines:
        # # OTA_BOTTOM_LEFT = (0.483, -2.423)
        # # OTA_TOP_RIGHT   = (3.367, 1.953)
        if {[regexp {OTA_BOTTOM_LEFT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set yBL $y
        }
        if {[regexp {OTA_TOP_RIGHT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set yTR $y
        }
    }
    close $fp

    if {$yBL eq "" || $yTR eq ""} {
        error "Failed to parse OTA_BOTTOM_LEFT / OTA_TOP_RIGHT Y from: $fname"
    }
    return [list $yBL $yTR]
}

# ----------------------------
# MAIN
# ----------------------------
proc place_m3_by_unique_nets_from_m2_txt {} {
    set design [_getEditDesign]
    if {$design eq ""} {
        error "No active edit design found. Open a layout and make it active."
    }
    if {![file exists $::IN_M2_FILE]} {
        error "IN_M2_FILE not found: $::IN_M2_FILE"
    }

    set recs [_readM2DumpFile $::IN_M2_FILE]
    if {[llength $recs] == 0} {
        error "Parsed 0 records from IN_M2_FILE. Check file formatting."
    }

    # Read OTA bbox Y edges (FULL HEIGHT TARGET)
    lassign [_readOtaBBox $::IN_OTA_FILE] otaYBL otaYTR
    if {$otaYTR <= $otaYBL} {
        error "Invalid OTA Y span parsed: otaYBL=$otaYBL otaYTR=$otaYTR"
    }

    # Global X span of M2 metals
    set xllMin ""
    set xurMax ""

    # Unique nets in encounter order
    set uniqueNets {}

    foreach r $recs {
        lassign $r net xll yll xur yur yc

        if {$::SKIP_NO_NET && $net eq "NO_NET"} { continue }

        if {$xllMin eq "" || $xll < $xllMin} { set xllMin $xll }
        if {$xurMax eq "" || $xur > $xurMax} { set xurMax $xur }

        if {[lsearch -exact $uniqueNets $net] == -1} {
            lappend uniqueNets $net
        }
    }

    set numNets [llength $uniqueNets]
    if {$numNets == 0} {
        error "No nets found (after SKIP_NO_NET filtering)."
    }
    if {$xllMin eq "" || $xurMax eq ""} {
        error "Failed to compute global X span."
    }

    set m2Width [expr {$xurMax - $xllMin}]
    if {$m2Width <= 0.0} {
        error "Invalid M2 width computed: $m2Width"
    }
    set dx [expr {$m2Width / double($numNets)}]

    puts "INFO: Unique nets=$numNets  M2_width=$m2Width  dx_slot=$dx  Xspan=($xllMin .. $xurMax)"
    puts "INFO: FORCING FULL OTA HEIGHT: OTA_YBL=$otaYBL  OTA_YTR=$otaYTR"

    set fpOut [_openOutTxt $::OUT_M3_FILE]

    set created 0
    for {set k 0} {$k < $numNets} {incr k} {
        set net [lindex $uniqueNets $k]

        # Slot center X for this net
        set xc [expr {$xllMin + ($k + 0.5) * $dx}]

        # ALWAYS span full OTA height
        set y1 $otaYBL
        set y2 $otaYTR

        # M3 rectangle box
        set halfW [expr {$::M3_WIDTH / 2.0}]
        set m3_xll [expr {$xc - $halfW}]
        set m3_xur [expr {$xc + $halfW}]
        set m3_yll $y1
        set m3_yur $y2

        set box [list [list $m3_xll $m3_yll] [list $m3_xur $m3_yur]]

        set obj ""
        if {[catch { set obj [le::createRectangle $box -design $design -lpp $::LPP_M3 -net $net] } err]} {
            puts "WARN: failed to create M3 for net=$net err=$err"
            continue
        }

        incr created

        puts $fpOut [format "%-6d %-24s %12.6f %12.6f %12.6f %12.6f %12.6f %6.3f..%6.3f %10.6f" \
            $created $net $m3_xll $m3_yll $m3_xur $m3_yur $xc $y1 $y2 $dx]
    }

    puts $fpOut ""
    puts $fpOut [format "SUMMARY: created=%d uniqueNets=%d M2width=%.6f dxSlot=%.6f OTA_YBL=%.6f OTA_YTR=%.6f M3_WIDTH=%.6f" \
        $created $numNets $m2Width $dx $otaYBL $otaYTR $::M3_WIDTH]
    close $fpOut

    puts "DONE: created $created M3 rectangles. Output coords: $::OUT_M3_FILE"
}

# Run
place_m3_by_unique_nets_from_m2_txt
