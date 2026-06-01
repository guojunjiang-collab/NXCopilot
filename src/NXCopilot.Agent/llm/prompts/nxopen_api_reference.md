# NXOpen Python API 参考

## Session
```python
import NXOpen
session = NXOpen.Session.GetSession()
work_part = session.Parts.Work
```

## Expression
```python
expr = work_part.Expressions.FindObject("p1")
unit = work_part.UnitCollection.FindObject("MilliMeter")
work_part.Expressions.EditWithUnits(expr, unit, "25")
```

## Features
```python
for feat in work_part.Features:
    print(feat.Name, feat.FeatureType)
feat = work_part.Features.FindObject("EXTRUDE(1)")
feat.Suppressed = True
work_part.Features.DeleteFeature(feat)
work_part.Update()
```
