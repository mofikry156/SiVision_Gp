############################################################
# place_m2_grid_from_bboxfile.tcl
#
# Reads first-script output:
#   INST_NAME ORIGIN_X ORIGIN_Y BBOX_LL_X BBOX_LL_Y BBOX_UR_X BBOX_UR_Y
#
# Finds OTA bounds from:
#   # OTA_BOTTOM_LEFT = (x, y)
#   # OTA_TOP_RIGHT   = (x, y)
#
# Groups devices into rows by similar URY (top Y),
# then places M2 straps at fixed offsets below row-URY:
#   URY - 0.129, -0.240, -0.400, -0.526
#
# Straps span OTA width exactly.
############################################################

# ---- user settings ----
set inFile "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"
set outFile "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"

set strapHeight 0.03
set rowTol      0.01
# X inset from OTA edges for straps
set xInset 0.101

set endOffset 0.100   ;# for first & last row only

# Middle rows offsets (your new set)
set offsets [list 0.101 0.172 0.249 0.393 0.463 0.533]
set offsets [lsort -real $offsets]


# ---- helpers ----
proc isNumber {s} { return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s] }

proc deleteFig {fig} {
    if {$fig eq ""} { return }
    if {[llength [info commands le::delete]]} { catch { le::delete $fig } ; return }
    if {[llength [info commands db::destroy]]} { catch { db::destroy $fig } ; return }
    if {[llength [info commands db::delete]]} { catch { db::delete $fig } ; return }
}

# trial-create a tiny rect to learn what -lpp accepts
proc resolveM2LPP {design} {
    set candidates [list \
        {M2 drawing} "M2 drawing" "M2:drawing" \
        {M2} "M2" \
        {metal2 drawing} "metal2 drawing" "METAL2:drawing" \
    ]
    set testBox [list [list 0.001 0.001] [list 0.002 0.002]]
    foreach lpp $candidates {
        set fig ""
        if {![catch { set fig [le::createRectangle $testBox -design $design -lpp $lpp] } err]} {
            deleteFig $fig
            puts "Resolved M2 LPP format as: $lpp"
            return $lpp
        }
    }
    error "Could not resolve a working -lpp value for M2. Add your PDK layer name to candidates in resolveM2LPP()."
}

proc createM2Strap {design lpp x0 y0 x1 y1} {
    set box [list [list $x0 $y0] [list $x1 $y1]]
    if {[catch { le::createRectangle $box -design $design -lpp $lpp } err]} {
        puts "WARN: Could not create rect. LPP=$lpp BB={$x0 $y0} {$x1 $y1}  err=$err"
    }
}

# quantize row key
proc quantKey {y tol} {
    return [expr {round($y / $tol) * $tol}]
}

# ---- main ----
set ctx    [de::getActiveContext]
set design [db::getAttr editDesign -of $ctx]
set lppM2  [resolveM2LPP $design]

set fp [open $inFile "r"]
set rp [open $outFile "w"]

# parse OTA bounds + collect row topYs
set otaLLX ""
set otaLLY ""
set otaURX ""
set otaURY ""

array set rowTopY {}  ;# rowTopY(key) = representative_ury
set lineNo 0
set good 0
set bad  0

while {[gets $fp line] >= 0} {
    incr lineNo
    set line [string trim $line]
    if {$line eq ""} { continue }

    # OTA parsing
    if {[regexp {^#\s*OTA_BOTTOM_LEFT\s*=\s*\(([^,]+),\s*([^)]+)\)} $line -> x y]} {
        set otaLLX [string trim $x]
        set otaLLY [string trim $y]
        continue
    }
    if {[regexp {^#\s*OTA_TOP_RIGHT\s*=\s*\(([^,]+),\s*([^)]+)\)} $line -> x y]} {
        set otaURX [string trim $x]
        set otaURY [string trim $y]
        continue
    }

    # skip headers/comments
    if {[string match "INST_NAME*" $line]} { continue }
    if {[string match "#*" $line]} { continue }

    # split cols
    set parts [regexp -all -inline {\S+} $line]
    if {[llength $parts] < 7} {
        incr bad
        puts $rp "SKIP line $lineNo (too few cols): $line"
        continue
    }

    # columns: 0 inst, 1 ox, 2 oy, 3 llx, 4 lly, 5 urx, 6 ury
    set ury [lindex $parts 6]
    if {![isNumber $ury]} {
        incr bad
        puts $rp "SKIP line $lineNo (non-numeric URY): $line"
        continue
    }

    set key [quantKey $ury $rowTol]

    # keep the maximum URY seen for this row key (stable for mixed small variations)
    if {![info exists rowTopY($key)]} {
        set rowTopY($key) $ury
    } else {
        if {$ury > $rowTopY($key)} { set rowTopY($key) $ury }
    }

    incr good
}

close $fp

# sanity OTA
if {$otaLLX eq "" || $otaURX eq "" || ![isNumber $otaLLX] || ![isNumber $otaURX]} {
    error "Could not parse OTA_BOTTOM_LEFT / OTA_TOP_RIGHT from file. Ensure those footer lines exist."
}

puts $rp "# place_m2_grid_from_bboxfile.tcl report"
puts $rp "# inFile=$inFile"
puts $rp "# otaLL=($otaLLX,$otaLLY) otaUR=($otaURX,$otaURY)"
puts $rp "# rowTol=$rowTol strapHeight=$strapHeight offsets=$offsets"
puts $rp "# lppM2=$lppM2"
puts $rp "# parsed good=$good bad=$bad rows=[llength [array names rowTopY]]"
puts $rp ""

# create straps per row
set keys [lsort -real [array names rowTopY]]
set nRows [llength $keys]

for {set i 0} {$i < $nRows} {incr i} {
    set key  [lindex $keys $i]
    set topY $rowTopY($key)

    # Decide which offsets to use:
    # - first row and last row: only endOffset (0.1)
    # - middle rows: your normal offsets list
    if {$i == 0 || $i == ($nRows - 1)} {
        set useOffsets [list $endOffset]
    } else {
        set useOffsets $offsets
    }

    foreach off $useOffsets {
        set yC [expr {$topY - $off}]
        set y0 [expr {$yC - $strapHeight/2.0}]
        set y1 [expr {$yC + $strapHeight/2.0}]

        # full width exactly
        # inset width (not full OTA width)
	set x0 [expr {$otaLLX + $xInset}]
	set x1 [expr {$otaURX - $xInset}]

	# safety
	if {$x1 <= $x0} {
    		error "Bad X span after inset: x0=$x0 x1=$x1 (check xInset vs OTA width)"
}

createM2Strap $design $lppM2 $x0 $y0 $x1 $y1

puts $rp "ROW $i/[expr {$nRows-1}]  TOP=$topY  off=$off  Yc=$yC  BB=($x0 $y0)-($x1 $y1)"

    }
}

close $rp
puts "Done. Placed M2 grid straps. Report: $outFile"

