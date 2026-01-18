########################################################################
# place_m3_by_unique_nets_from_m2_txt.tcl
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
# PLACEMENT RULES:
#   - One M3 per UNIQUE net (remove duplicates: vdd!,vdd!,vdd! => one).
#   - Compute total M2 width from global min(XLL) and max(XUR).
#   - Horizontal spacing dx = M2_width / numUniqueNets.
#   - Assign each net a unique Xc = XLL_min + (k+0.5)*dx.
#   - M3 height per net:
#       * If net occurs >1: span = [min(YLL) .. max(YUR)]
#       * If net occurs 1:  stub around YC with SINGLE_NET_STUB_H
#   - SPECIAL MIN-LEN RULE:
#       * If computed M3 length < MIN_M3_LEN:
#           - if net occurs >1  => force length = FORCED_M3_LEN_MULTI
#           - if net occurs ==1 => force length = FORCED_M3_LEN_SINGLE
#       * Forced length is centered around the original (y1..y2) midpoint.
#
# NEW RULE (your latest):
#   - For any net whose name does NOT contain substring NET_SUBSTRING (default "net"):
#       * Try to extend the M3 vertically toward the nearer OTA edge (top or bottom)
#       * Only apply if resulting length <= MAX_M3_EXTENDED_LEN (default 2.7)
#       * If extension would exceed MAX_M3_EXTENDED_LEN, keep original (y1..y2)
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
set M3_WIDTH 0.034

# Optional extra margin on top/bottom of M3 (helps guarantee overlap)
set M3_MARGIN_Y 0.000

# If a net appears only once, create a "stub" height around that one stripe:
# total stub height = SINGLE_NET_STUB_H (centered on that stripe's YC)
set SINGLE_NET_STUB_H 0.080

# Skip nets named NO_NET if present
set SKIP_NO_NET 1

# ---- MIN-LENGTH POLICY ----
# If computed M3 length < MIN_M3_LEN:
#   - multi-occ net: force length FORCED_M3_LEN_MULTI
#   - single-occ net: force length FORCED_M3_LEN_SINGLE
set MIN_M3_LEN            0.15
set FORCED_M3_LEN_SINGLE  0.02
set FORCED_M3_LEN_MULTI   0.45

# ---- OTA EDGE EXTENSION POLICY (ONLY for nets NOT containing NET_SUBSTRING) ----
# If net name does NOT contain NET_SUBSTRING:
#   - extend toward nearer OTA edge (top/bottom) if resulting length <= MAX_M3_EXTENDED_LEN
#   - otherwise keep original y-span
set NET_SUBSTRING         "net"
set MAX_M3_EXTENDED_LEN   2.7

# ----------------------------
# HELPERS
# ----------------------------
proc isNumber {s} {
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

    # Read OTA bbox Y edges
    lassign [_readOtaBBox $::IN_OTA_FILE] otaYBL otaYTR

    # Global X span of M2 metals
    set xllMin ""
    set xurMax ""

    # Per-net stats
    array set ymin {}
    array set ymax {}
    array set cnt  {}
    array set yc1  {}

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

        if {![info exists cnt($net)]} {
            set cnt($net) 1
            set ymin($net) $yll
            set ymax($net) $yur
            set yc1($net) $yc
        } else {
            incr cnt($net)
            if {$yll < $ymin($net)} { set ymin($net) $yll }
            if {$yur > $ymax($net)} { set ymax($net) $yur }
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
    puts "INFO: MIN_M3_LEN=$::MIN_M3_LEN  forced(single)=$::FORCED_M3_LEN_SINGLE  forced(multi)=$::FORCED_M3_LEN_MULTI"
    puts "INFO: OTA_YBL=$otaYBL OTA_YTR=$otaYTR  NET_SUBSTRING=$::NET_SUBSTRING  MAX_M3_EXTENDED_LEN=$::MAX_M3_EXTENDED_LEN"

    set fpOut [_openOutTxt $::OUT_M3_FILE]

    set created 0
    for {set k 0} {$k < $numNets} {incr k} {
        set net [lindex $uniqueNets $k]

        # Slot center X for this net
        set xc [expr {$xllMin + ($k + 0.5) * $dx}]

        # Compute initial Y span for this net
        if {[info exists cnt($net)] && $cnt($net) > 1} {
            set y1 [expr {$ymin($net) - $::M3_MARGIN_Y}]
            set y2 [expr {$ymax($net) + $::M3_MARGIN_Y}]
        } else {
            set halfH [expr {$::SINGLE_NET_STUB_H / 2.0}]
            set yCenter $yc1($net)
            set y1 [expr {$yCenter - $halfH}]
            set y2 [expr {$yCenter + $halfH}]
        }

        # ---- Enforce min-length rule (as you had) ----
        set curLen [expr {$y2 - $y1}]
        if {$curLen < $::MIN_M3_LEN} {
            set yCenter [expr {($y1 + $y2) / 2.0}]
            if {[info exists cnt($net)] && $cnt($net) > 1} {
                set halfForced [expr {$::FORCED_M3_LEN_MULTI / 2.0}]
            } else {
                set halfForced [expr {$::FORCED_M3_LEN_SINGLE / 2.0}]
            }
            set y1 [expr {$yCenter - $halfForced}]
            set y2 [expr {$yCenter + $halfForced}]
        }

        # ---- NEW: OTA edge extension for nets that do NOT contain NET_SUBSTRING ----
        # Try to extend toward nearer OTA edge (top/bottom) if resulting length <= MAX_M3_EXTENDED_LEN
        if {[string first $::NET_SUBSTRING $net] == -1} {
            set yMid [expr {($y1 + $y2) / 2.0}]
            set dBot [expr {abs($yMid - $otaYBL)}]
            set dTop [expr {abs($yMid - $otaYTR)}]

            set newY1 $y1
            set newY2 $y2

            if {$dBot <= $dTop} {
                # extend downward to bottom edge, keep upper end fixed
                set newY1 $otaYBL
                set newY2 $y2
            } else {
                # extend upward to top edge, keep lower end fixed
                set newY1 $y1
                set newY2 $otaYTR
            }

            set newLen [expr {$newY2 - $newY1}]
            if {$newLen > 0.0 && $newLen <= $::MAX_M3_EXTENDED_LEN} {
                set y1 $newY1
                set y2 $newY2
            } else {
                # Too tall or invalid: keep the original (y1,y2)
            }
        }

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
    puts $fpOut [format "SUMMARY: created=%d uniqueNets=%d M2width=%.6f dxSlot=%.6f MIN_M3_LEN=%.6f forced(single)=%.6f forced(multi)=%.6f OTA_YBL=%.6f OTA_YTR=%.6f NET_SUBSTRING=%s MAX_M3_EXTENDED_LEN=%.6f" \
        $created $numNets $m2Width $dx $::MIN_M3_LEN $::FORCED_M3_LEN_SINGLE $::FORCED_M3_LEN_MULTI $otaYBL $otaYTR $::NET_SUBSTRING $::MAX_M3_EXTENDED_LEN]
    close $fpOut

    puts "DONE: created $created M3 rectangles. Output coords: $::OUT_M3_FILE"
}

# Run
place_m3_by_unique_nets_from_m2_txt

