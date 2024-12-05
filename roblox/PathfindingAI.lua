-- Services
local Debris = game:GetService('Debris')
local Pathfinding = game:GetService('PathfindingService')
local RunService = game:GetService("RunService")

-- Types
export type State = {
	Name : string,
	Func : "function"
}

-- Modules
local States = require(script.Parent.States)

--[[
KNOWN ISSUES

1. If the AI spawns and there is an enemy directly in front of it when it is initalized, it just won't do anything for some random amount of time.
This is only sometime reproduceable and sometimes nothing happens at all. Really have very little ideas as to what might cause this? Overall
it shouldn't really cause any problems though.

2. After a while the AI stops doing anything and just freezes? No other information provided.
	This is likely caused by a player getting spotted while the AI is attempting to go back to idle on a node.
	
3. Animations don't play. No other information provided

]]

-- Class
local AI = {
	Target = nil,
	State = States.Idle,
	
	DebugRoutine = nil, -- Coroutine for debug
	MoveRoutine = nil,
	
	AttackCooldown = false,
	TicksUnseen = 0,
	
	LastNode = nil,
	
	Parameters = {
		-- Misc
		Debug = false, -- IF DEBUG IS ON THE MODEL WILL NOT FACE THE MOVE DIRECTION
		ConeVisualizationType = 0, 
		--[[
		0: Show all rays from cones
		1: Show only rays hitting objects
		2: Don't show rays
		]]
		-- Fastest task.wait is .015
		RayRefreshSpeed = .1, -- in seconds
		TrackRayRefreshSpeed = .05, -- ^ 
		EnemyDetectColor = Color3.fromRGB(0, 85, 0),
		ObjectDetectColor = Color3.fromRGB(96, 96, 96),
		
		-- Distances in studs, FOV in degrees
		-- Chase area
		ChaseRadius = 100,
		DebugCRC = Color3.fromRGB(8, 74, 140),
		
		-- Forward facing detection cone
		ForwardDist = 45,
		ForwardFOV = 135,
		RayCountForward = 68, -- Ray count will impact performance
		DebugFFOVC = Color3.fromRGB(123, 13, 13),
			
		-- Back facing detection cone
		RearDist = 43,
		RearFOV = 30,
		RayCountBack = 25,
		DebugRFOVC = Color3.fromRGB(197, 8, 157),
		
		-- Kill Radius
		KillRadius = 8,
		DebugKRC = Color3.fromRGB(18, 100, 17),
		
		-- AI Stats
		Health = 2000,
		Damage = 999,
		WalkSpeed = 9,
		AttackSpeed = .5, -- Time between attacks in seconds
		MaxUnseenSeconds = 1, -- Number of seconds of memory the AI has 
		
		MaxMoveDistance = 100, -- The max distance the AI will look for nodes in
		MinRoamWaitTime = 4,
		MaxRoamWaitTime = 10,
		
		-- Pathfinding 
		Pathfinding = {
			AgentRadius = 2,
			AgentHeight = 5,
			AgentCanJump = false,
			AgentCanClimb = false,
			WaypointSpacing = 4,
			Costs = {},
		},
		
		PathUpdateThreshold = 5,
		DoorOpenDistance = 5,
		
		-- Animations
		ChaseAnimDistance = 35, -- How close the enemy has to be to a player for the chase animation to play
		
		-- Nodes folder
		Nodes = workspace.SCP_Nodes,
		
		-- Home node
		HomeNode = workspace.SCP_Nodes.SCP049_Home_Node,
		
		-- Animations
		Animations = nil,
	}
}
AI.__index = AI

-- Constructor

function AI.New(Name: string, Model: Instance, Parameters : AIParameters)
	local self = setmetatable({}, AI)
	self.Name = Name or "Unknown"
	self.Model = Model
	if not Model then
		-- Except when no model provided
		error("Error: No model provided")
	end
	
	-- For showing whenever an enemy is in range visually
	self.ChaseRadiusVisualizer = nil
	self.KillRadiusVisualizer = nil
	
	-- Swap parameters for custom instead of default
	if Parameters then
		for ParameterName, Value in Parameters do
			self.Parameters[ParameterName] = Value
		end
	end
	
	-- Get bounding size
	self.BoundingBox = self:GetModelSize()
	
	-- Setup stats
	Model.Name = self.Name
	Model.Humanoid.Health = self.Parameters.Health
	Model.Humanoid.WalkSpeed = self.Parameters.WalkSpeed
	
	self.CurrentTrack = nil -- This relates to animations actually
	
	-- Audio stuff
	self.AudioList = {}
	for _, AudioType in pairs(self.Model.AI.Audio:GetChildren()) do
		self.AudioList[AudioType.Name] = AudioType:GetChildren()
	end
	
	-- Setting up and playing footsteps
	task.spawn(function()
		while task.wait(.45) do
			-- Checking if the AI has an animation currently playing that isn't the idle animation
			if self.CurrentTrack and self.CurrentTrack ~= self.Tracks.Idle then
				self:PlayAudio("Walk")
			end
		end
	end)
	
	
	self:AnimationHandler()
	
	-- Fire initial state
	self.State.Func(self)
	return self
end

-- Function to check if the hit instance belongs to a player
local function WasPlayerHit(instance)
	while instance.Parent do
		if instance.Parent:FindFirstChild("Humanoid") then
			return instance.Parent
		end
		if instance.Parent == workspace then return nil end
		instance = instance.Parent
	end
	return nil
end

function AI:CastRays()
	task.spawn(function()
		local NumRaysForward = self.Parameters.RayCountForward
		local NumRaysBackward = self.Parameters.RayCountBack

		-- Sizes
		local ForwardDist = self.Parameters.ForwardDist
		local BackwardsDist = self.Parameters.RearDist

		-- Angles
		local ForwardAngle = math.rad(self.Parameters.ForwardFOV)
		local BackwardsAngle = math.rad(self.Parameters.RearFOV)

		-- Parameters
		local raycastParams = RaycastParams.new()
		raycastParams.FilterType = Enum.RaycastFilterType.Exclude
		raycastParams.FilterDescendantsInstances = {self.Model}

		while self.State == States.Idle do
			task.wait(self.Parameters.RayRefreshSpeed)
			local AngleStepForward = ForwardAngle / (NumRaysForward - 1)
			local AngleStepBackward = BackwardsAngle / (NumRaysBackward - 1)

			for i = 0, NumRaysForward - 1 do
				local Origin = self.Model.Head.Position - Vector3.new(0, 1, 0)
				local Direction = self.Model.PrimaryPart.CFrame.LookVector.Unit
				local CurrentAngle = -ForwardAngle / 2 + i * AngleStepForward
				-- Calculate RayDirection correctly
				local RayDirection = (CFrame.Angles(0, CurrentAngle, 0) * CFrame.new(Direction)).Position
				RayDirection = RayDirection.Unit -- Ensure the direction vector is normalized

				local rayResult = workspace:Raycast(Origin, RayDirection * ForwardDist, raycastParams)
				local RayPart = nil
				if self.Parameters.Debug and self.Parameters.ConeVisualizationType == 0 then
					RayPart = Instance.new("Part")
					RayPart.Size = Vector3.new(0.2, 0.2, ForwardDist)
					RayPart.CanCollide = false
					RayPart.Transparency = .75
					RayPart.Color = self.Parameters.DebugFFOVC
					RayPart.Parent = self.Model.AI.VisualizedCones
					
					RayPart.CFrame = CFrame.new(Origin, Origin + RayDirection) * CFrame.new(0, 0, -ForwardDist / 2)

					local Weld = Instance.new('WeldConstraint')
					Weld.Parent = RayPart
					Weld.Part0 = RayPart
					Weld.Part1 = self.Model.PrimaryPart
					
					Debris:AddItem(RayPart, self.Parameters.RayRefreshSpeed + .1)
				end

				if not rayResult then continue end
				if self.Parameters.Debug and RayPart then
					RayPart.Size = Vector3.new(0.2, 0.2, rayResult.Distance)
					RayPart.WeldConstraint:Destroy()
					RayPart.CFrame = CFrame.new(Origin, Origin + RayDirection) * CFrame.new(0, 0, -rayResult.Distance / 2)
					RayPart.Transparency = .35
					local Weld = Instance.new('WeldConstraint')
					Weld.Parent = RayPart
					Weld.Part0 = RayPart
					Weld.Part1 = self.Model.PrimaryPart
				elseif self.Parameters.Debug and self.Parameters.ConeVisualizationType == 1 then
					RayPart = Instance.new("Part")
					RayPart.Size = Vector3.new(0.2, 0.2, rayResult.Distance)
					RayPart.CanCollide = false
					RayPart.Transparency = .35
					RayPart.Color = self.Parameters.DebugFFOVC
					RayPart.Parent = self.Model.AI.VisualizedCones

					RayPart.CFrame = CFrame.new(Origin, Origin + RayDirection) * CFrame.new(0, 0, -rayResult.Distance / 2)

					local Weld = Instance.new('WeldConstraint')
					Weld.Parent = RayPart
					Weld.Part0 = RayPart
					Weld.Part1 = self.Model.PrimaryPart

					Debris:AddItem(RayPart, self.Parameters.RayRefreshSpeed + .05)
				end
				local Target = WasPlayerHit(rayResult.Instance)
				if Target then
					if Target.Humanoid.Health <= 0 then return end
					self.Target = Target
					self:SetState(States.Chase)
					if not self.Parameters.Debug then return end
					RayPart.Color = self.Parameters.EnemyDetectColor
					return
				else
					-- Don't do anything because it's not a player
					if not self.Parameters.Debug then continue end
					RayPart.Color = self.Parameters.ObjectDetectColor
				end
			end
			
			for i = 0, NumRaysBackward - 1 do
				local Origin = self.Model.Head.Position - Vector3.new(0, 1, 0)
				local Direction = -self.Model.PrimaryPart.CFrame.LookVector.Unit
				local CurrentAngle = -BackwardsAngle / 2 + i * AngleStepBackward
				-- Calculate RayDirection correctly
				local RayDirection = (CFrame.Angles(0, CurrentAngle, 0) * CFrame.new(Direction)).Position
				RayDirection = RayDirection.Unit -- Ensure the direction vector is normalized

				local rayResult = workspace:Raycast(Origin, RayDirection * BackwardsDist, raycastParams)

				if not rayResult then continue end
				local Target = WasPlayerHit(rayResult.Instance)
				if Target then
					-- Sanity checks (dead or crouching)
					if Target.Humanoid.Health <= 0 then return end
					local PlayingAnimTracks = Target.Humanoid.Animator:GetPlayingAnimationTracks()
					local Crouched = false
					for _, Anim in pairs(PlayingAnimTracks) do
						if Anim.Animation.AnimationId == "rbxassetid://16129126390" then
							Crouched = true 
						end
					end
					if Crouched then
						continue
					else
						self.Target = Target
						self:SetState(States.Chase)
						return
					end
				else
					-- Don't do anything because it's not a player
					if not self.Parameters.Debug then continue end
				end
			end
		end

	end)
	
end

function getRandomNode(AI) : Vector3
	local NearbyNodes = {}
	for _, Node in pairs(AI.Parameters.Nodes) do
		if AI.LastNode then
			-- Don't allow the AI to go to the same node twice
			if AI.LastNode == Node then continue end
		end
		
		local Distance = (AI.Model.HumanoidRootPart.Position - Node.Position).Magnitude
		if Distance <= AI.Parameters.MaxMoveDistance then
			table.insert(NearbyNodes, Node)
		end
	end
	
	-- In case there is no nodes nearby, default to the "HomeNode"
	if #NearbyNodes <= 0 then
		warn(`INFO: SCP {AI.Name} can't find any other nodes to pathfind to. Returning it to the home node.`)
		return AI.Parameters.HomeNode
	end
	local NodeIndex = math.random(1, #NearbyNodes)

	AI.LastNode = NearbyNodes[NodeIndex]
	return NearbyNodes[NodeIndex]
end

local function StopAnimations(AI)
	local RunningAnimations = AI.Model.Humanoid:GetPlayingAnimationTracks()
	for i, animation in pairs(RunningAnimations) do
		if animation.IsPlaying == true then
			animation:Stop()
		end	
	end
	
	AI.Tracks.Idle:Play()
	AI.CurrentTrack = AI.Tracks.Idle
end

function AI:Roam()
	if self.MoveRoutine then return end
	local MoveToPart = getRandomNode(self)
	
	local Path : Path = Pathfinding:CreatePath(self.Parameters.Pathfinding)
	local Success, Err = pcall(function()
		Path:ComputeAsync(self.Model.PrimaryPart.Position, MoveToPart.Position)
	end)
	
	local Distance = 15
	local RayParams = RaycastParams.new()
	RayParams.FilterDescendantsInstances = {self.Model}
	RayParams.FilterType = Enum.RaycastFilterType.Exclude
	
	local ElevatorConnection 
	-- Potential connection for elevator behavior regarding teleporting when touching certain nodes.
	-- Also, to note, there should probably be a specific contact group between these elevator nodes and the SCPs
	
	if string.find(string.lower(MoveToPart.Name), "elevator") then
		ElevatorConnection = MoveToPart.Touched:Connect(function(TouchedPart)
			if TouchedPart.Parent or TouchedPart.Parent.Parent == self.Model then
				self.Model:MoveTo(MoveToPart.LinkedNode.Value.Position)
				self.Model.Humanoid:MoveTo(self.Model.HumanoidRootPart.Position)
				self.State = States.Idle
				ElevatorConnection:Disconnect()
			end
		end)
	end

	if Success and Path.Status == Enum.PathStatus.Success then
		local Waypoints = Path:GetWaypoints()
		local CurrentPathIndex = 2
		
		local function Pathfind(callback)
			local CurrentPoint = Waypoints[CurrentPathIndex]
			local MoveToPoint = CurrentPoint.Position
			
			local Origin = self.Model.HumanoidRootPart.Position
			local Direction = self.Model.HumanoidRootPart.CFrame.LookVector
			
			-- Check if there is a door in the way
			local RayResult = workspace:Raycast(Origin, Direction * Distance, RayParams)
			if RayResult then
				if RayResult.Instance.Parent:GetAttribute("Opened") ~= nil then
					RayResult.Instance.Parent:SetAttribute("Opened", true)
				end
			end
			
			self.Model.Humanoid:MoveTo(MoveToPoint)
			self.Model.Humanoid.MoveToFinished:Wait()
			
			CurrentPathIndex+= 1
			if CurrentPathIndex <= #Waypoints and self.State == States.Idle then
				-- If the AI should continue moving
				Pathfind(callback)
			else
				callback()
			end
		end
		
		self.MoveRoutine = task.spawn(function()
			if self.State ~= States.Idle then 
				return 
			end
			
			local function callback()
				if self.Parameters.Debug then warn("INFO: Idle roam final waypoint reached.") end
				StopAnimations(self)
				if self.State == States.Idle then
					task.wait(math.random(self.Parameters.MinRoamWaitTime, self.Parameters.MaxRoamWaitTime))
					self.MoveRoutine = nil
					self:Roam()
				else
					self.MoveRoutine = nil
				end
			end
			
			Pathfind(callback)
		end)
		
	elseif not Success then
		warn("ERR: Error when generating path: " .. Err)
	elseif Path.Status == Enum.PathStatus.NoPath then
		warn("ERR: Error when generating path: No path")
	end
end

function AI:TrackEnemy()
	-- Clear movement so it doesn't interfere with tracking
	if self.MoveRoutine or self.State ~= States.Chase then 
		task.cancel(self.MoveRoutine)
		self.MoveRoutine = nil 
	end
	
	-- Play the spotting audio
	self:PlayAudio("Spot")

	local raycastParams = RaycastParams.new()
	raycastParams.FilterType = Enum.RaycastFilterType.Exclude
	raycastParams.FilterDescendantsInstances = {self.Model}
	
	-- Reset the TicksUnseen number
	self.TicksUnseen = 0
	
	-- Only continue if the AI is actively chasing and there is a target
	if self.State ~= States.Chase or not self.Target then return end
	
	-- Create the initial pathfinding data
	local Path : Path = Pathfinding:CreatePath(self.Parameters.Pathfinding)
	
	local Success, Err = pcall(function()
		Path:ComputeAsync(self.Model.PrimaryPart.Position, self.Target.HumanoidRootPart.Position)
	end)
	
	if not Success or Err then
		warn(`ERR: AI {self.Name} had an error when creating its path to the target: {Err}`)
		self:SetState(States.Idle)
		return
	end

	local Waypoints = Path:GetWaypoints()
	local NextWaypointIndex
	local ReachedConnection
	local BlockedConnection
	
	local OutOfVision = false
	local ResumeRoam = false
	
	-- Create an event based system to move to the next waypoint
	local function MoveAlongPath()
		-- Before anything else, check if the enemy is still a valid target
		if self.State ~= States.Chase or not self.Target then return end
		
		BlockedConnection = Path.Blocked:Connect(function(BlockedWaypointIndex)
			-- Check if the obstacle is further down the path
			if BlockedWaypointIndex >= NextWaypointIndex then
				local Success, Err = pcall(function()
					Path:ComputeAsync(self.Model.PrimaryPart.Position, self.Target.HumanoidRootPart.Position)
				end)
				
				if not Success or Err then
					warn(`ERR: AI {self.Name} had an error when creating its path to the target: {Err}`)
					self:SetState(States.Idle)
					return
				end
				
				Waypoints = Path:GetWaypoints()
				NextWaypointIndex = 2
				BlockedConnection:Disconnect()
				MoveAlongPath()
			end
		end)

		if not ReachedConnection then
			ReachedConnection = self.Model.Humanoid.MoveToFinished:Connect(function(Reached)
				if Reached and NextWaypointIndex < #Waypoints then
					-- Check to make sure moving is still valid
					if self.State ~= States.Chase or not self.Target then 
						ReachedConnection:Disconnect()
						BlockedConnection:Disconnect()
						return 
					end
					-- Increase waypoint index and move to next waypoint
					-- Check if the enemy moved
					local TargetMoved = (self.Target.HumanoidRootPart.Position - Waypoints[#Waypoints].Position).Magnitude > self.Parameters.PathUpdateThreshold
					if TargetMoved and not OutOfVision then
						local Success, Err = pcall(function()
							Path:ComputeAsync(self.Model.PrimaryPart.Position, self.Target.HumanoidRootPart.Position)
						end)

						if not Success or Err then
							warn(`ERR: AI {self.Name} had an error when creating its path to the target: {Err}`)
							self:SetState(States.Idle)
							return
						end

						Waypoints = Path:GetWaypoints()
						NextWaypointIndex = 2
						BlockedConnection:Disconnect()
						MoveAlongPath()
					else
						NextWaypointIndex += 1
						self.Model.Humanoid:MoveTo(Waypoints[NextWaypointIndex].Position)
					end
				elseif Reached and NextWaypointIndex == #Waypoints then
					-- Reached the player's position
					ReachedConnection:Disconnect()
					BlockedConnection:Disconnect()
					
					if self:Attack() then
						warn("Attack successful!")
						self:SetState(States.Idle)
						return
					else
						warn("Attack unsuccessful")
						if OutOfVision then
							task.wait(1)
							if not OutOfVision then warn("Refound the enemy!"); MoveAlongPath() end
							warn("Can't find the enemy")
							ResumeRoam = true
							self:SetState(States.Idle)
							return
						else
							warn("Refound the enemy!")
							MoveAlongPath()
						end
					end
				else		
					ReachedConnection:Disconnect()
					BlockedConnection:Disconnect()
				end
			end)
		end

		-- Move along the path
		NextWaypointIndex = 2
		if not Waypoints[NextWaypointIndex] then return end
		self.Model.Humanoid:MoveTo(Waypoints[NextWaypointIndex].Position)
	end
	
	local s, e = pcall(MoveAlongPath)
	if not s or e then warn(e) end
	
	-- Create a loop that ensures the AI is chasing and has a target
	while self.State == States.Chase and self.Target do
		print("A")
		task.wait(self.Parameters.TrackRayRefreshSpeed)

		-- Then, we create the raycast to check if the enemy is within vision
		local Origin = self.Model.Head.Position - Vector3.new(0, 1, 0)
		if not self.Target.Humanoid then return end; if self.Target.Humanoid.Health <= 0 then return end
		local Direction = CFrame.lookAt(Origin, self.Target.HumanoidRootPart.Position).LookVector
		local Distance = (Origin - self.Target.HumanoidRootPart.Position).Magnitude

		local RayResult = workspace:Raycast(Origin, Direction * (Distance + 1), raycastParams)

		-- Changing this behavior, now the AI will check if it sees the enemy, and if the AI doesn't it will go to their last known location and try to reacquire a target. If they don't get a target, they'll just go back
		-- to roaming like normal
		if not RayResult then
			OutOfVision = true
			continue
		end

		-- Check if the player was hit by the ray, and then do the same as above
		if not WasPlayerHit(RayResult.Instance) then
			OutOfVision = true
			continue
		end
		
		OutOfVision = false
		
		if ResumeRoam then
			return
		end

	end
	
end

function AI:GetModelSize(): Vector3
	local minX, minY, minZ = math.huge, math.huge, math.huge
	local maxX, maxY, maxZ = -math.huge, -math.huge, -math.huge

	for _, part in ipairs(self.Model:GetDescendants()) do
		if part:IsA("BasePart") then
			local size = part.Size
			local cframe = part.CFrame
			local corners = {
				cframe * CFrame.new(-size.X / 2, -size.Y / 2, -size.Z / 2),
				cframe * CFrame.new(size.X / 2, -size.Y / 2, -size.Z / 2),
				cframe * CFrame.new(-size.X / 2, size.Y / 2, -size.Z / 2),
				cframe * CFrame.new(size.X / 2, size.Y / 2, -size.Z / 2),
				cframe * CFrame.new(-size.X / 2, -size.Y / 2, size.Z / 2),
				cframe * CFrame.new(size.X / 2, -size.Y / 2, size.Z / 2),
				cframe * CFrame.new(-size.X / 2, size.Y / 2, size.Z / 2),
				cframe * CFrame.new(size.X / 2, size.Y / 2, size.Z / 2)
			}
			for _, corner in ipairs(corners) do
				local pos = corner.Position
				if pos.X < minX then minX = pos.X end
				if pos.Y < minY then minY = pos.Y end
				if pos.Z < minZ then minZ = pos.Z end
				if pos.X > maxX then maxX = pos.X end
				if pos.Y > maxY then maxY = pos.Y end
				if pos.Z > maxZ then maxZ = pos.Z end
			end
		end
	end

	return Vector3.new(maxX - minX, maxY - minY, maxZ - minZ)
end
	
function AI:Attack()
	-- Slight sanity checks
	local AttackSuccessful = false
	if not self.Target then
		self:SetState(States.Idle)
		return AttackSuccessful
	end
	
	if self.Target.Humanoid.Health > 0 and self.Model.Humanoid.Health > 0 and not self.AttackCooldown then
		-- Find the distance and ensure its valid
		local Origin = self.Model.Head.Position - Vector3.new(0, 1, 0)
		local Distance = (Origin - self.Target.HumanoidRootPart.Position).Magnitude
		
		if Distance <= self.Parameters.KillRadius then
			self.Target.Humanoid:TakeDamage(self.Parameters.Damage)
			self.AttackCooldown = true
			task.wait(self.Parameters.AttackSpeed)
			self.AttackCooldown = false
			self.Target = nil
			AttackSuccessful = true
		end
	end
	
	return AttackSuccessful
end

function AI:AnimationHandler()
	if not self.Parameters.Animations then 
		warn("No animations provided.")
		return 
	end
	local Humanoid = self.Model.Humanoid
	local Animator = Humanoid.Animator
	
	print(self.Parameters.Animations)
	
	self.Tracks = {}
	
	local function IsPlaying(Track)
		local CurrentlyPlayingAnims = Humanoid:GetPlayingAnimationTracks()
		for _, CurrentTrack in pairs(CurrentlyPlayingAnims) do
			if CurrentTrack == Track then
				return true
			end
		end
		return false
	end
	
	for AnimName, AnimId in pairs(self.Parameters.Animations) do
		local NewAnim = Instance.new("Animation")
		NewAnim.AnimationId = AnimId
		local NewTrack = Animator:LoadAnimation(NewAnim)
		self.Tracks[AnimName] = NewTrack
	end
	
	Humanoid:GetPropertyChangedSignal("WalkToPoint"):Connect(function()
		local Humanoid_State = Humanoid:GetState()
		local DistanceToEnemy = math.huge
		if self.Target then
			DistanceToEnemy = (self.Model.HumanoidRootPart.Position - self.Target.HumanoidRootPart.Position).Magnitude
		end
		
		if Humanoid_State == Enum.HumanoidStateType.Running and not IsPlaying(self.Tracks.NormalWalk) and DistanceToEnemy > self.Parameters.ChaseAnimDistance then
			if self.CurrentTrack then self.CurrentTrack:Stop() end
			self.Tracks.NormalWalk:Play()
			self.CurrentTrack = self.Tracks.NormalWalk
		elseif Humanoid_State == Enum.HumanoidStateType.Running and not IsPlaying(self.Tracks.AttackWalk) and self.Target and DistanceToEnemy <= self.Parameters.ChaseAnimDistance then
			if self.CurrentTrack then self.CurrentTrack:Stop() end
			self.Tracks.AttackWalk:Play()
			self.CurrentTrack = self.Tracks.AttackWalk
		end
	end)
end

function AI:PlayAudio(AudioType)
	local AudioList = self.AudioList
	
	local Passed = false
	for ValidType, _ in pairs(AudioList) do
		if ValidType == AudioType then
			Passed = true
			break
		end
	end
	if not Passed then warn(`ERR: "{AudioType}" is not a valid audio type`) return end
	
	local Track = math.random(1, #AudioList[AudioType])
	AudioList[AudioType][Track]:Play()
	
end

--[[
Handles the switching of states, including validating the state and running the functions of state
]]
function AI:SetState(NewState : State)
	local StateValid = false
	for _, Table in pairs(States) do
		if NewState == Table then
			StateValid = true
			break
		end
	end
	if not StateValid or NewState == self.State then
		warn("ERR: Invalid state provided: ".. NewState.Name)
		if NewState == self.State then
			warn("^ INFO: State already switched to.")
		end
		return
	end
	
	if self.MoveRoutine then
		warn("INFO: MoveRoutine canceled")
		task.cancel(self.MoveRoutine)
		StopAnimations(self)
		self.MoveRoutine = nil
	end
	
	self.State = NewState
	NewState.Func(self)
end

return AI
