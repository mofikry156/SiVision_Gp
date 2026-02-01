########################################################################
# edge_taps_only_NETCONNECT_PG.tcl
#
# TAPS ONLY (EDGE rows):
# 1) Parse report for EDGE approach rows
# 2) Find the nearest (by row index distance) neighboring strap whose net.sigType
#    is POWER or GROUND
# 3) Inherit REAL net connectivity by copying that neighbor's net object:
#       db::setAttr net -of $edgeObj -value $netObj
# 4) (Optional) also write user attr "name" as "{vdd!}" for visibility/debug
# 5) Place CreateVias every STEP_X along the EDGE strap
########################################################################

set REPORT_FILE "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"

# --- Parameters ---
set LPP_M2       {M2 drawing}
set VIA_DEF      "VIA12"
set VIA_ORIENT   "R0"
set STEP_X       0.074
set X_FROM_LEFT  0.02
set X_FROM_RIGHT 0.03
set MAX_TRIES    3000

# Optional: also stamp user attr name as "{net}" (does NOT affect connectivity)
set ALSO_SET_USER_NAME_ATTR 1

# ----------------------------
# Helpers
# ----------------------------
proc _isNumber {s} {
  return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc _safeGetAttr {attr obj} {
  set v ""
  if {$obj eq ""} { return "" }
  if {![catch { set v [db::getAttr $attr -of $obj] }]} { return $v }
  return ""
}

proc _isPowerOrGround {sigType} {
  set s [string tolower $sigType]
  return [expr {$s eq "power" || $s eq "ground"}]
}

proc _findStrapObj {design lpp xll yll xur yur} {
  set tol 0.0005
  set sh [db::getShapes -of $design -lpp $lpp -filter {%type=="Rect"}]
  db::foreach s $sh {
    set bb ""
    if {[catch { set bb [db::getAttr bBox -of $s] }]} { continue }
    lassign [lindex $bb 0] s_xll s_yll
    lassign [lindex $bb 1] s_xur s_yur
    if {abs($s_xll-$xll) < $tol && abs($s_yll-$yll) < $tol &&
        abs($s_xur-$xur) < $tol && abs($s_yur-$yur) < $tol} {
      return $s
    }
  }
  return ""
}

# user attr name="{net}" (debug/optional)
proc _setUserNameAttrBraced {obj netName} {
  if {$obj eq "" || $netName eq ""} { return 0 }
  set bracedName "{$netName}"
  set ok 0
  if {![catch { db::setAttr name -of $obj -value $bracedName }]} {
    set ok 1
  } else {
    if {![catch { db::addAttr name -of $obj -valueType string -value $bracedName }]} {
      set ok 1
    }
  }
  puts "      userAttr(name)='[_safeGetAttr name $obj]' (target='$bracedName')"
  return $ok
}

# REAL "naming": connect strap to neighbor net object
proc _inheritNeighborNet {edgeObj neighborObj} {
  if {$edgeObj eq "" || $neighborObj eq ""} { return 0 }

  set netObj ""
  if {[catch { set netObj [db::getAttr net -of $neighborObj] } err]} {
    puts "      WARN: cannot read neighbor net object: $err"
    return 0
  }
  if {$netObj eq ""} {
    puts "      WARN: neighbor has empty net object (not connected)."
    return 0
  }

  if {[catch { db::setAttr net -of $edgeObj -value $netObj } err2]} {
    puts "      WARN: failed to set net on edge strap: $err2"
    return 0
  }

  puts "      EDGE net now name='[_safeGetAttr net.name $edgeObj]' sigType='[_safeGetAttr net.sigType $edgeObj]'"
  return 1
}

# Find closest POWER/GROUND neighbor row strap (search outward from ridx)
# For row 0, we search downward; for last row, upward; otherwise both directions.
proc _findNearestPGNeighborObj {design ridx rowStrapsArr rowApproachArr} {
  array set rowStraps $rowStrapsArr
  array set rowApproach $rowApproachArr

  # Determine search directions
  set maxRow -1
  foreach r [array names rowStraps] {
    if {$r > $maxRow} { set maxRow $r }
  }

  # Search expanding radius: 1,2,3...
  for {set d 1} {$d <= $maxRow} {incr d} {
    set candidates {}

    # Prefer inward direction for edge rows:
    # top edge (ridx==0): check ridx+d
    # bottom edge (ridx==maxRow): check ridx-d
    if {$ridx == 0} {
      lappend candidates [expr {$ridx + $d}]
    } elseif {$ridx == $maxRow} {
      lappend candidates [expr {$ridx - $d}]
    } else {
      # middle edge (if any): check both sides
      lappend candidates [expr {$ridx - $d}] [expr {$ridx + $d}]
    }

    foreach nr $candidates {
      if {![info exists rowStraps($nr)]} { continue }
      if {[llength $rowStraps($nr)] == 0} { continue }

      # Use first strap in that row
      set nData [lindex $rowStraps($nr) 0]
      set nObj [_findStrapObj $design $::LPP_M2 \
        [dict get $nData xll] [dict get $nData yll] [dict get $nData xur] [dict get $nData yur]]

      if {$nObj eq ""} { continue }

      set sigType [_safeGetAttr "net.sigType" $nObj]
      set netName [_safeGetAttr "net.name" $nObj]

      if {$sigType eq "" || $netName eq ""} { continue }
      if {![_isPowerOrGround $sigType]} {
        # not power/ground, skip
        continue
      }

      return $nObj
    }
  }

  return ""
}

# ----------------------------
# Parser (same format as your report)
# ----------------------------
proc _parseReportByRow {fname} {
  if {![file exists $fname]} { error "REPORT_FILE not found: $fname" }

  array set rowApproach {}
  array set rowStraps {}

  set fp [open $fname r]
  while {[gets $fp line] >= 0} {
    set raw $line
    set line [string trim $line]
    if {$line eq ""} continue

    # Parse approach lines from comments too
    if {[string match "#*" $line]} {
      if {[regexp {ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+APPROACH=([A-Z0-9_]+)} $line -> ridx topVal appr]} {
        set rowApproach($ridx) $appr
      } elseif {[regexp {ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+(APPROACH[0-9]+)} $line -> ridx topVal appr2]} {
        set rowApproach($ridx) $appr2
      }
      continue
    }

    # Strap lines
    if {[regexp {^ROW\s+([0-9]+)/[0-9]+\s+TOP=([-\d\.]+)\s+off=([-\d\.]+)\s+Yc=([-\d\.]+)\s+BB=\(([-\d\.]+)\s+([-\d\.]+)\)-\(([-\d\.]+)\s+([-\d\.]+)\)} \
         $line -> ridx topVal offVal yc xll yll xur yur]} {

      foreach v [list $topVal $offVal $yc $xll $yll $xur $yur] {
        if {$v eq "" || ![_isNumber $v]} {
          puts "WARN: Skipping malformed strap line: $raw"
          continue 2
        }
      }

      set strap [dict create row $ridx top $topVal off $offVal yc $yc xll $xll yll $yll xur $xur yur $yur]
      if {![info exists rowStraps($ridx)]} { set rowStraps($ridx) {} }
      lappend rowStraps($ridx) $strap
    }
  }
  close $fp

  return [list [array get rowApproach] [array get rowStraps]]
}

# ----------------------------
# Main (EDGE rows only)
# ----------------------------
proc run_edge_taps_only {} {
  set ctx    [de::getActiveContext]
  set design [db::getAttr editDesign -of $ctx]
  if {$design eq ""} { error "No edit design found." }

  lassign [_parseReportByRow $::REPORT_FILE] approachArr strapsArr
  array set rowApproach $approachArr
  array set rowStraps   $strapsArr

  foreach ridx [lsort -integer [array names rowStraps]] {
    set approach ""
    if {[info exists rowApproach($ridx)]} { set approach $rowApproach($ridx) }

    # EDGE rows only
    if {![string match "EDGE*" $approach] && $approach ne "EDGE"} { continue }

    puts "ROW $ridx: EDGE row detected. Searching nearest POWER/GROUND neighbor..."

    set pgNeighborObj [_findNearestPGNeighborObj $design $ridx $strapsArr $approachArr]
    if {$pgNeighborObj eq ""} {
      puts "ROW $ridx: WARN: no POWER/GROUND neighbor found; skipping."
      continue
    }

    set targetNet [_safeGetAttr "net.name" $pgNeighborObj]
    set sigType   [_safeGetAttr "net.sigType" $pgNeighborObj]
    puts "ROW $ridx: EDGE -> inherit $sigType net='$targetNet'"

    # Process each strap in EDGE row (usually 1)
    foreach strap $rowStraps($ridx) {
      set xll [dict get $strap xll]
      set yll [dict get $strap yll]
      set xur [dict get $strap xur]
      set yur [dict get $strap yur]
      set yc  [dict get $strap yc]

      set edgeObj [_findStrapObj $design $::LPP_M2 $xll $yll $xur $yur]
      if {$edgeObj eq ""} {
        puts "   WARN: EDGE strap not found for BB=($xll $yll)-($xur $yur)"
        continue
      }

      puts "   EDGE strap found. Inheriting REAL net from POWER/GROUND neighbor..."
      if {![_inheritNeighborNet $edgeObj $pgNeighborObj]} {
        puts "   WARN: Could not inherit net; skipping via placement for this strap."
        continue
      }

      if {$::ALSO_SET_USER_NAME_ATTR} {
        # purely optional - does not affect connectivity
        _setUserNameAttrBraced $edgeObj $targetNet
      }

      # --- PLACE CreateVias iteratively ---
      set xStart [expr {$xur - $::X_FROM_RIGHT}]
      set xStop  [expr {$xll + $::X_FROM_LEFT}]
      set vCount 0
      set tries  0

      for {set x $xStart} {$x >= $xStop} {set x [expr {$x - $::STEP_X}]} {
        incr tries
        if {$tries > $::MAX_TRIES} { break }

        set pt [list $x $yc]
        if {![catch { le::createVia -design $design -definition $::VIA_DEF -origin $pt -orient $::VIA_ORIENT } v]} {
          incr vCount
        }
      }

      puts "   Done: $vCount createVias placed on EDGE row $ridx (net='$targetNet')."
    }
  }
}

# Run
run_edge_taps_only

